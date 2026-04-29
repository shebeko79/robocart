package com.robocart.data.network

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.IOException
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetSocketAddress
import java.net.SocketTimeoutException

private const val CONNECTION_EXPIRE_TIMEOUT_SEC = 60L
private const val KEEP_ALIVE_PERIOD_SEC = 10L

class UdpTransport(
    private val hostName: String?,
    private val port: Int,
    private val initialAddress: InetSocketAddress? = null,
    private val onJson: (Any?) -> Unit = {},
    private val onJpeg: (ByteArray) -> Unit = {},
    private val onAck: (Int) -> Unit = {},
    key: ByteArray? = null,
) : PacketProcessor() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val lock = Any()
    private var loopJob: Job? = null
    private var socket: DatagramSocket? = null
    private var address: InetSocketAddress? = null
    private var receivedCandidatePacketNumber = 0
    private var lastSendTimeSec = 0L
    private val aes = key?.copyOf()?.let(::AesPack)

    init {
        isCrypted = aes != null
        address = initialAddress
    }

    fun start() {
        if (loopJob?.isActive == true) {
            return
        }
        if (address != null && socket == null) {
            socket = DatagramSocket().apply {
                soTimeout = 50
            }
        }
        loopJob = scope.launch {
            while (isActive) {
                processTick()
                delay(50)
            }
        }
    }

    suspend fun stop() {
        loopJob?.cancel()
        loopJob = null
        closeSocket()
        synchronized(lock) {
            packets.clear()
        }
    }

    fun isAlive(): Boolean = address != null && lastReceivedPacketNumber > 0

    fun sendJson(payload: Map<String, Any?>) {
        synchronized(lock) {
            enqueueChunk(packJson(payload))
        }
    }

    private fun processTick() {
        val nowSec = System.currentTimeMillis() / 1000
        if (nowSec >= lastReceivedTimeSec + CONNECTION_EXPIRE_TIMEOUT_SEC) {
            address = null
            closeSocket()
        }

        if (address == null) {
            if (!resolveAddress()) {
                return
            }
            lastReceivedPacketNumber = 0
            receivedCandidatePacketNumber = 0
            lastReceivedTimeSec = nowSec
            lastSendTimeSec = 0
        }

        synchronized(lock) {
            if (packets.isEmpty() && nowSec >= lastSendTimeSec + KEEP_ALIVE_PERIOD_SEC) {
                enqueueChunk(packJson(emptyMap()))
            }
        }

        sendPendingPacket(nowSec)
        receiveAvailablePacket(nowSec)
    }

    private fun resolveAddress(): Boolean {
        val hn = hostName ?: return false
        return try {
            val resolved = InetSocketAddress(hn, port)
            if (resolved.address == null) {
                return false
            }
            address = resolved
            closeSocket()
            socket = DatagramSocket().apply {
                soTimeout = 50
            }
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun sendPendingPacket(nowSec: Long) {
        val sock = socket ?: return
        val dst = address ?: return
        val packet = synchronized(lock) { pack() } ?: return
        try {
            sock.send(DatagramPacket(packet, packet.size, dst))
            lastSendTimeSec = nowSec
        } catch (_: IOException) {
            address = null
            closeSocket()
        }
    }

    private fun receiveAvailablePacket(nowSec: Long) {
        val sock = socket ?: return
        val dst = address ?: return
        val incoming = ByteArray(65536)
        val datagram = DatagramPacket(incoming, incoming.size)
        try {
            sock.receive(datagram)
        } catch (_: SocketTimeoutException) {
            return
        } catch (_: IOException) {
            address = null
            closeSocket()
            return
        }

        if (datagram.address?.hostAddress != dst.address.hostAddress || datagram.port != dst.port) {
            return
        }

        val data = datagram.data.copyOf(datagram.length)
        val packetNumber = getPacketNumber(data) ?: return
        if (isPacketTooOld(packetNumber)) {
            return
        }

        receivedCandidatePacketNumber = packetNumber
        if (parse(data)) {
            lastReceivedTimeSec = nowSec
            lastReceivedPacketNumber = packetNumber
        }
    }

    private fun closeSocket() {
        socket?.close()
        socket = null
    }

    override fun crypt(bytes: ByteArray): ByteArray = aes?.crypt(bytes) ?: bytes

    override fun decrypt(bytes: ByteArray, packetNumber: Int): ByteArray? = aes?.decrypt(bytes) ?: bytes

    override fun processJson(payload: Any?) {
        onJson(payload)
    }

    override fun processJpeg(payload: ByteArray) {
        onJpeg(payload)
        synchronized(lock) {
            enqueueChunk(packAck(receivedCandidatePacketNumber))
        }
    }

    override fun processAck(ackPacketNumber: Int) {
        onAck(ackPacketNumber)
    }
}
