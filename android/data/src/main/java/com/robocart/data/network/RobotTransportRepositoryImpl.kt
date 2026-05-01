package com.robocart.data.network

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.net.wifi.WifiManager
import android.util.Log
import com.robocart.domain.connection.RobotTransportRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.net.InetSocketAddress
import java.util.concurrent.atomic.AtomicBoolean

class RobotTransportRepositoryImpl(
    context: Context,
    private val port: Int,
    private val key: ByteArray? = null,
    private val serviceType: String = "_robocart._udp.",
    private val serviceNamePrefix: String = "robocart",
) : RobotTransportRepository {
    private companion object {
        const val TAG = "RobocartTransport"
        const val RELAY_HOST = "93.127.143.124"
        const val DISCOVERY_TO_RELAY_TIMEOUT_MS = 3000L
    }

    private val appContext: Context = context.applicationContext
    private val nsdManager: NsdManager =
        appContext.getSystemService(Context.NSD_SERVICE) as NsdManager
    private val wifiManager: WifiManager =
        appContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val jsonFlow = MutableSharedFlow<Any?>(extraBufferCapacity = 64)
    private val jpegFlow = MutableSharedFlow<ByteArray>(extraBufferCapacity = 8)
    private val connectedFlow = MutableStateFlow(false)
    private val relayConnectionFlow = MutableStateFlow(false)

    private var transport: UdpTransport? = null
    private var monitorJob: Job? = null
    private var currentAddress: InetSocketAddress? = null

    private val discoveryActive = AtomicBoolean(false)
    private var discoveryRetryJob: Job? = null
    private var relayFallbackJob: Job? = null
    private var multicastLock: WifiManager.MulticastLock? = null

    private val discoveryListener = object : NsdManager.DiscoveryListener {
        override fun onDiscoveryStarted(serviceType: String) {
            // no-op
        }

        override fun onServiceFound(serviceInfo: NsdServiceInfo) {
            if (transport != null) {
                return
            }
            if (serviceInfo.serviceType != serviceType) {
                return
            }
            val name = serviceInfo.serviceName.orEmpty()
            if (serviceNamePrefix.isNotBlank() && !name.startsWith(serviceNamePrefix, ignoreCase = true)) {
                return
            }
            Log.d(TAG, "Service found: name=$name type=${serviceInfo.serviceType} port=${serviceInfo.port}")
            nsdManager.resolveService(serviceInfo, resolveListener)
        }

        override fun onServiceLost(serviceInfo: NsdServiceInfo) {
            // ignore: we treat resolved service as a connection target.
        }

        override fun onDiscoveryStopped(serviceType: String) {
            discoveryActive.set(false)
        }

        override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) {
            discoveryActive.set(false)
            Log.w(TAG, "Discovery failed: type=$serviceType errorCode=$errorCode")
            scheduleDiscoveryRetry()
        }

        override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) {
            discoveryActive.set(false)
            Log.w(TAG, "Discovery stop failed: type=$serviceType errorCode=$errorCode")
            scheduleDiscoveryRetry()
        }
    }

    private val resolveListener = object : NsdManager.ResolveListener {
        override fun onResolveFailed(serviceInfo: NsdServiceInfo, errorCode: Int) {
            // ignore and wait for another resolved service
            Log.w(TAG, "Resolve failed: name=${serviceInfo.serviceName} type=${serviceInfo.serviceType} errorCode=$errorCode")
        }

        override fun onServiceResolved(serviceInfo: NsdServiceInfo) {
            val hostInetAddress = serviceInfo.host
            val resolvedPort = serviceInfo.port
            Log.d(TAG, "Service resolved: host=${hostInetAddress?.hostAddress ?: "null"} port=$resolvedPort")
            if (resolvedPort != port) {
                return
            }

            val initialAddress = hostInetAddress?.let { InetSocketAddress(it, resolvedPort) } ?: return
            val newHostName = hostInetAddress?.hostName ?: hostInetAddress?.hostAddress

            val shouldCreateTransport =
                transport == null ||
                    currentAddress?.hostString != initialAddress.hostString ||
                    currentAddress?.port != initialAddress.port

            if (!shouldCreateTransport) {
                return
            }

            currentAddress = initialAddress

            scope.launch {
                relayFallbackJob?.cancel()
                relayFallbackJob = null
                relayConnectionFlow.value = false
                transport?.stop()
                transport = UdpTransport(
                    hostName = newHostName,
                    port = resolvedPort,
                    initialAddress = initialAddress,
                    onJson = { payload ->
                        jsonFlow.tryEmit(payload)
                        connectedFlow.value = true
                    },
                    onJpeg = { payload ->
                        jpegFlow.tryEmit(payload)
                        connectedFlow.value = true
                    },
                    key = key,
                )
                transport?.start()
            }
        }
    }

    override val jsonEvents: Flow<Any?> = jsonFlow.asSharedFlow()
    override val jpegEvents: Flow<ByteArray> = jpegFlow.asSharedFlow()
    override val isConnected: Flow<Boolean> = connectedFlow.asStateFlow()
    override val isRelayConnection: Flow<Boolean> = relayConnectionFlow.asStateFlow()

    override fun start() {
        acquireMulticastLock()

        if (monitorJob?.isActive != true) {
            monitorJob = scope.launch {
                while (isActive) {
                    connectedFlow.value = transport?.isAlive() == true
                    delay(250)
                }
            }
        }

        if (transport == null) {
            startDiscoveryIfNeeded()
            scheduleRelayFallback()
        }
    }

    override suspend fun stop() {
        discoveryRetryJob?.cancel()
        discoveryRetryJob = null
        relayFallbackJob?.cancel()
        relayFallbackJob = null

        discoveryActive.set(false)
        try {
            nsdManager.stopServiceDiscovery(discoveryListener)
        } catch (_: Exception) {
            // ignore
        }

        multicastLock?.let {
            try {
                it.release()
            } catch (_: Exception) {
                // ignore
            }
        }
        multicastLock = null

        monitorJob?.cancel()
        monitorJob = null

        transport?.stop()
        transport = null
        currentAddress = null

        connectedFlow.value = false
        relayConnectionFlow.value = false
    }

    override fun sendJson(payload: Map<String, Any?>) {
        transport?.sendJson(payload)
    }

    private fun acquireMulticastLock() {
        if (multicastLock != null) return
        try {
            multicastLock = wifiManager.createMulticastLock("robocart_nsd").apply {
                setReferenceCounted(true)
                acquire()
            }
        } catch (_: Exception) {
            // Some builds/devices may require extra permissions; discovery will just fail.
            multicastLock = null
        }
    }

    private fun startDiscoveryIfNeeded() {
        if (!discoveryActive.compareAndSet(false, true)) {
            return
        }
        try {
            nsdManager.discoverServices(serviceType, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        } catch (_: Exception) {
            discoveryActive.set(false)
            scheduleDiscoveryRetry()
        }
    }

    private fun scheduleDiscoveryRetry() {
        discoveryRetryJob?.cancel()
        discoveryRetryJob = scope.launch {
            delay(1500)
            if (transport == null && !discoveryActive.get()) {
                startDiscoveryIfNeeded()
                scheduleRelayFallback()
            }
        }
    }

    private fun scheduleRelayFallback() {
        relayFallbackJob?.cancel()
        relayFallbackJob = scope.launch {
            delay(DISCOVERY_TO_RELAY_TIMEOUT_MS)
            if (transport != null) {
                return@launch
            }

            val relayAddress = InetSocketAddress(RELAY_HOST, port)
            currentAddress = relayAddress
            relayConnectionFlow.value = true
            Log.i(TAG, "LAN service not found, switching to relay host=$RELAY_HOST port=$port")

            transport?.stop()
            transport = UdpTransport(
                hostName = RELAY_HOST,
                port = port,
                initialAddress = relayAddress,
                onJson = { payload ->
                    jsonFlow.tryEmit(payload)
                    connectedFlow.value = true
                },
                onJpeg = { payload ->
                    jpegFlow.tryEmit(payload)
                    connectedFlow.value = true
                },
                key = key,
            )
            transport?.start()
        }
    }
}
