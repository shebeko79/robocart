package com.robocart.data.network

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

class ProtocolCompatibilityTest {
    private class TestProcessor(key: ByteArray? = null) : PacketProcessor() {
        val receivedJson = mutableListOf<Any?>()
        var receivedJpeg = ByteArray(0)
        var lastAck = -1
        private val aes = key?.let(::AesPack)

        init {
            isCrypted = aes != null
        }

        fun nextOutgoingPacket(): ByteArray? = pack()

        fun queueJpeg(data: ByteArray) {
            enqueueChunk(packChunk(data, PacketType.JPG))
        }

        fun queueJson(payload: Map<String, Any?>) {
            enqueueChunk(packJson(payload))
        }

        fun queueJson(payload: String) {
            enqueueChunk(packJson(payload))
        }

        fun queueAck(packetNumber: Int) {
            enqueueChunk(packAck(packetNumber))
        }

        fun receive(packet: ByteArray) {
            val packetNumber = getPacketNumber(packet) ?: return
            if (isPacketTooOld(packetNumber)) {
                return
            }
            if (parse(packet)) {
                lastReceivedPacketNumber = packetNumber
            }
        }

        override fun crypt(bytes: ByteArray): ByteArray = aes?.crypt(bytes) ?: bytes

        override fun decrypt(bytes: ByteArray, packetNumber: Int): ByteArray? = aes?.decrypt(bytes) ?: bytes

        override fun processJson(payload: Any?) {
            receivedJson += payload
        }

        override fun processJpeg(payload: ByteArray) {
            receivedJpeg = payload
        }

        override fun processAck(ackPacketNumber: Int) {
            lastAck = ackPacketNumber
        }
    }

    @Test
    fun aesPack_roundTripsPayload() {
        val key = ByteArray(16) { (it + 1).toByte() }
        val aes1 = AesPack(key)
        val aes2 = AesPack(key)
        val payload = ByteArray(32_000) { (it % 251).toByte() }

        repeat(5) {
            val crypt1 = aes1.crypt(payload)
            val decrypted1 = aes2.decrypt(crypt1)
            assertArrayEquals(payload, decrypted1)

            val crypt2 = aes2.crypt(payload)
            val decrypted2 = aes1.decrypt(crypt2)
            assertArrayEquals(payload, decrypted2)
        }
    }

    @Test
    fun packetProcessor_handlesFragmentedJpegPayload() {
        val sender = TestProcessor()
        val receiver = TestProcessor()
        val jpeg = ByteArray(PacketProcessor.MAX_PACKET_SIZE * 2 + 7) { i -> (i % 256).toByte() }

        sender.queueJpeg(jpeg)
        pipe(sender, receiver)

        assertArrayEquals(jpeg, receiver.receivedJpeg)
    }

    @Test
    fun packetProcessor_matchesDesktopScenariosForLengthsAndJsonOrdering() {
        val lengths = buildList {
            add(1)
            add(2)
            add(256)
            add(1024)
            for (delta in -6..5) {
                add(PacketProcessor.MAX_PACKET_SIZE + delta)
            }
            for (delta in -6..5) {
                add(PacketProcessor.MAX_PACKET_SIZE * 2 + delta)
            }
            add(65_000)
            add(100_000)
        }
        val beforeJson = """{"before":1}"""
        val afterJson = """{"after":1}"""

        for (length in lengths) {
            runJpegFlowScenario(
                key = null,
                jpegLength = length,
                addBeforeJson = false,
                addAfterJson = false,
                beforeJson = beforeJson,
                afterJson = afterJson,
            )
            runJpegFlowScenario(
                key = null,
                jpegLength = length,
                addBeforeJson = true,
                addAfterJson = false,
                beforeJson = beforeJson,
                afterJson = afterJson,
            )
            runJpegFlowScenario(
                key = null,
                jpegLength = length,
                addBeforeJson = false,
                addAfterJson = true,
                beforeJson = beforeJson,
                afterJson = afterJson,
            )
            runJpegFlowScenario(
                key = null,
                jpegLength = length,
                addBeforeJson = true,
                addAfterJson = true,
                beforeJson = beforeJson,
                afterJson = afterJson,
            )
        }
    }

    @Test
    fun packetProcessor_processesAckChunks() {
        val sender = TestProcessor()
        val receiver = TestProcessor()
        sender.queueAck(0x1234)

        pipe(sender, receiver)

        assertEquals(0x1234, receiver.lastAck)
    }

    @Test
    fun packetProcessor_requiresFollowupPacketForPartialChunk() {
        val sender = TestProcessor()
        val receiver = TestProcessor()
        val jpeg = ByteArray(PacketProcessor.MAX_PACKET_SIZE * 2 + 32) { i -> (i % 251).toByte() }
        sender.queueJpeg(jpeg)

        val firstPacket = sender.nextOutgoingPacket()
        assertTrue(firstPacket != null)
        receiver.receive(firstPacket!!)
        assertEquals(0, receiver.receivedJpeg.size)

        pipe(sender, receiver)
        assertArrayEquals(jpeg, receiver.receivedJpeg)
    }

    @Test
    fun packetProcessor_encryptedModeRemainsCompatible() {
        val key = Random(42).nextBytes(16)
        val sender = TestProcessor(key)
        val receiver = TestProcessor(key)
        val jpeg = ByteArray(65_000) { i -> (i % 127).toByte() }

        sender.queueJpeg(jpeg)
        pipe(sender, receiver)

        assertArrayEquals(jpeg, receiver.receivedJpeg)
    }

    @Test
    fun packetProcessor_encryptedModeMatchesDesktopScenarios() {
        val key = Random(42).nextBytes(16)
        val lengths = listOf(1, PacketProcessor.MAX_PACKET_SIZE - 3, PacketProcessor.MAX_PACKET_SIZE + 3, 65_000)
        val beforeJson = """{"before":1}"""
        val afterJson = """{"after":1}"""

        for (length in lengths) {
            runJpegFlowScenario(
                key = key,
                jpegLength = length,
                addBeforeJson = true,
                addAfterJson = true,
                beforeJson = beforeJson,
                afterJson = afterJson,
            )
        }
    }

    private fun runJpegFlowScenario(
        key: ByteArray?,
        jpegLength: Int,
        addBeforeJson: Boolean,
        addAfterJson: Boolean,
        beforeJson: String,
        afterJson: String,
    ) {
        val sender = TestProcessor(key)
        val receiver = TestProcessor(key)
        val jpeg = ByteArray(jpegLength) { i -> (i % 256).toByte() }

        if (addBeforeJson) {
            sender.queueJson(beforeJson)
        }
        sender.queueJpeg(jpeg)
        if (addAfterJson) {
            sender.queueJson(afterJson)
        }

        pipe(sender, receiver)
        assertArrayEquals(jpeg, receiver.receivedJpeg)
    }

    private fun pipe(sender: TestProcessor, receiver: TestProcessor) {
        while (true) {
            val packet = sender.nextOutgoingPacket() ?: break
            receiver.receive(packet)
        }
    }
}
