package com.robocart.data.network

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

class RobotTransportRepositoryImpl(
    private val hostName: String,
    private val port: Int,
    private val key: ByteArray? = null,
) : RobotTransportRepository {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val jsonFlow = MutableSharedFlow<Any?>(extraBufferCapacity = 64)
    private val jpegFlow = MutableSharedFlow<ByteArray>(extraBufferCapacity = 8)
    private val connectedFlow = MutableStateFlow(false)

    private var transport: UdpTransport? = null
    private var monitorJob: Job? = null

    override val jsonEvents: Flow<Any?> = jsonFlow.asSharedFlow()
    override val jpegEvents: Flow<ByteArray> = jpegFlow.asSharedFlow()
    override val isConnected: Flow<Boolean> = connectedFlow.asStateFlow()

    override fun start() {
        if (transport == null) {
            transport = UdpTransport(
                hostName = hostName,
                port = port,
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
        }
        transport?.start()
        if (monitorJob?.isActive != true) {
            monitorJob = scope.launch {
                while (isActive) {
                    connectedFlow.value = transport?.isAlive() == true
                    delay(250)
                }
            }
        }
    }

    override suspend fun stop() {
        monitorJob?.cancel()
        monitorJob = null
        transport?.stop()
        connectedFlow.value = false
    }

    override fun sendJson(payload: Map<String, Any?>) {
        transport?.sendJson(payload)
    }
}
