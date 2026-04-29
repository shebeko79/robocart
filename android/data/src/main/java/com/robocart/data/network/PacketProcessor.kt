package com.robocart.data.network

import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener
import java.nio.charset.StandardCharsets
import kotlin.math.min

open class PacketProcessor {
    companion object {
        const val MAX_PACKET_SIZE = 1400
        const val MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - 3
    }

    data class PacketChunk(val type: PacketType, val payload: ByteArray)

    protected val packets = ArrayDeque<PacketChunk>()
    private var sendPacketNumber = 0
    protected var isCrypted = false
    private var sendPartialOffset = 0
    private var receivePartialChunk = ByteArray(0)
    protected var lastReceivedPacketNumber = 0
    protected var lastReceivedTimeSec = 0L

    protected fun pack(): ByteArray? {
        if (packets.isEmpty()) {
            return null
        }

        sendPacketNumber = getNextPacketNumber()
        var fitIt = 0
        var totalPayloadSize = 0
        for (chunk in packets) {
            var chunkLen = chunk.payload.size + 5
            if (fitIt == 0) {
                chunkLen -= sendPartialOffset
            }
            if (fitIt != 0 && totalPayloadSize + chunkLen > MAX_PAYLOAD_SIZE) {
                break
            }
            fitIt++
            totalPayloadSize += chunkLen
        }

        val firstChunkOversized = totalPayloadSize > MAX_PAYLOAD_SIZE
        if (firstChunkOversized) {
            totalPayloadSize = MAX_PAYLOAD_SIZE
        }

        var nextPartialOffset = sendPartialOffset
        val payload = ByteArray(totalPayloadSize)
        var offset = 0
        for (i in 0 until fitIt) {
            val packet = packets.elementAt(i)
            var chunkLen = packet.payload.size
            writeUInt32(payload, offset, chunkLen.toUInt())
            payload[offset + 4] = packet.type.wireValue.toByte()

            var chunkOffset = 0
            if (i == 0) {
                chunkOffset = sendPartialOffset
                chunkLen -= sendPartialOffset
            }

            val dataOffset = offset + 5
            if (dataOffset + chunkLen > totalPayloadSize) {
                chunkLen = totalPayloadSize - dataOffset
                nextPartialOffset += chunkLen
            } else {
                nextPartialOffset = 0
            }

            System.arraycopy(packet.payload, chunkOffset, payload, dataOffset, chunkLen)
            offset += chunkLen + 5
        }

        val finalPayload = if (isCrypted) crypt(payload) else payload
        val packet = ByteArray(finalPayload.size + 3)
        packet[0] = ((sendPacketNumber ushr 8) and 0xFF).toByte()
        packet[1] = (sendPacketNumber and 0xFF).toByte()
        packet[2] = if (sendPartialOffset != 0) 1 else 0
        System.arraycopy(finalPayload, 0, packet, 3, finalPayload.size)

        sendPartialOffset = nextPartialOffset
        if (!firstChunkOversized) {
            repeat(fitIt) { packets.removeFirst() }
        }
        return packet
    }

    fun packChunk(data: ByteArray, type: PacketType): PacketChunk = PacketChunk(type, data)

    fun packJson(json: String): PacketChunk = packChunk(json.toByteArray(StandardCharsets.UTF_8), PacketType.JSON)

    fun packJson(payload: Map<String, Any?>): PacketChunk {
        val jsonObject = JSONObject()
        payload.forEach { (key, value) ->
            jsonObject.put(key, toJsonValue(value))
        }
        return packJson(jsonObject.toString())
    }

    fun packAck(receivedPacketNumber: Int): PacketChunk {
        val bytes = byteArrayOf(
            ((receivedPacketNumber ushr 8) and 0xFF).toByte(),
            (receivedPacketNumber and 0xFF).toByte(),
        )
        return packChunk(bytes, PacketType.ACK)
    }

    fun enqueueChunk(chunk: PacketChunk) {
        packets.addLast(chunk)
    }

    fun enqueueJson(payload: Map<String, Any?>) {
        enqueueChunk(packJson(payload))
    }

    fun getPacketNumber(packet: ByteArray): Int? {
        if (packet.size < 2) {
            return null
        }
        return ((packet[0].toInt() and 0xFF) shl 8) or (packet[1].toInt() and 0xFF)
    }

    fun isPacketTooOld(packetNumber: Int): Boolean {
        return lastReceivedPacketNumber >= packetNumber &&
            !(packetNumber < 64 && lastReceivedPacketNumber > 65536 - 64)
    }

    fun parse(packet: ByteArray): Boolean {
        if (packet.size < 3) {
            return false
        }

        val packetNumber = getPacketNumber(packet) ?: return false
        val isNextPartial = packet[2].toInt() != 0
        if (isNextPartial && packetNumber != ((lastReceivedPacketNumber + 1) and 0xFFFF)) {
            return false
        }

        return if (isCrypted) {
            val payload = decrypt(packet.copyOfRange(3, packet.size), packetNumber) ?: return false
            parseInternal(payload, 0, isNextPartial)
        } else {
            parseInternal(packet, 3, isNextPartial)
        }
    }

    private fun parseInternal(packet: ByteArray, offset: Int, isNextPartial: Boolean): Boolean {
        if (!isNextPartial) {
            receivePartialChunk = ByteArray(0)
        }
        var receivedPartialLen = receivePartialChunk.size
        val totalLen = packet.size

        var i = offset
        var item = 0
        while (i < totalLen) {
            if (i + 5 > totalLen) {
                return false
            }
            var chunkLen = readUInt32(packet, i).toInt()
            if (item == 0) {
                if (chunkLen <= receivedPartialLen) {
                    return false
                }
                chunkLen -= receivedPartialLen
            }
            val nextI = i + 5 + chunkLen
            if (nextI > totalLen && item != 0) {
                // The trailing chunk may legitimately be partial; it will be completed by the next packet.
                break
            }
            i = nextI
            item++
        }

        i = offset
        item = 0
        while (i + 5 <= totalLen) {
            var chunkLen = readUInt32(packet, i).toInt()
            if (item == 0) {
                chunkLen -= receivedPartialLen
            }

            val nextI = i + 5 + chunkLen
            if (nextI > totalLen && item != 0) {
                break
            }

            var chunk = packet.copyOfRange(i + 5, min(i + 5 + chunkLen, totalLen))
            val chunkType = packet[i + 4].toInt() and 0xFF

            if (nextI > totalLen) {
                receivePartialChunk += chunk
                return true
            }

            if (item == 0) {
                chunk = receivePartialChunk + chunk
                receivePartialChunk = ByteArray(0)
                receivedPartialLen = 0
            }

            try {
                when (PacketType.fromWireValue(chunkType)) {
                    PacketType.JSON -> processJson(JSONTokener(String(chunk, StandardCharsets.UTF_8)).nextValue())
                    PacketType.JPG -> processJpeg(chunk)
                    PacketType.ACK -> {
                        if (chunk.size >= 2) {
                            val ackNumber = ((chunk[0].toInt() and 0xFF) shl 8) or (chunk[1].toInt() and 0xFF)
                            processAck(ackNumber)
                        }
                    }
                    null -> Unit
                }
            } catch (_: Exception) {
                // Keep parser resilient to malformed chunks, matching Python behavior.
            }
            i = nextI
            item++
        }
        return true
    }

    private fun getNextPacketNumber(): Int = (sendPacketNumber + 1) % 65536

    private fun writeUInt32(buffer: ByteArray, offset: Int, value: UInt) {
        buffer[offset] = ((value.toLong() ushr 24) and 0xFF).toByte()
        buffer[offset + 1] = ((value.toLong() ushr 16) and 0xFF).toByte()
        buffer[offset + 2] = ((value.toLong() ushr 8) and 0xFF).toByte()
        buffer[offset + 3] = (value.toLong() and 0xFF).toByte()
    }

    private fun readUInt32(buffer: ByteArray, offset: Int): UInt {
        val a = buffer[offset].toUByte().toUInt() shl 24
        val b = buffer[offset + 1].toUByte().toUInt() shl 16
        val c = buffer[offset + 2].toUByte().toUInt() shl 8
        val d = buffer[offset + 3].toUByte().toUInt()
        return a or b or c or d
    }

    protected open fun crypt(bytes: ByteArray): ByteArray = bytes

    protected open fun decrypt(bytes: ByteArray, packetNumber: Int): ByteArray? = bytes

    protected open fun processJson(payload: Any?) = Unit

    protected open fun processJpeg(payload: ByteArray) = Unit

    protected open fun processAck(ackPacketNumber: Int) = Unit

    private fun toJsonValue(value: Any?): Any? {
        return when (value) {
            null -> JSONObject.NULL
            is Map<*, *> -> {
                val obj = JSONObject()
                value.forEach { (k, v) ->
                    if (k is String) {
                        obj.put(k, toJsonValue(v))
                    }
                }
                obj
            }
            is Iterable<*> -> {
                val arr = JSONArray()
                value.forEach { arr.put(toJsonValue(it)) }
                arr
            }
            else -> value
        }
    }
}
