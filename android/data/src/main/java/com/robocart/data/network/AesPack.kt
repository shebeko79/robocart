package com.robocart.data.network

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec

class AesPack(key: ByteArray) {
    private val encryptNonceBytes = ByteArray(8).also { SecureRandom().nextBytes(it) }
    private val encryptNonce = readUInt64(encryptNonceBytes, 0)
    private var encryptSeq = ByteArray(0)
    private var decryptNonce: ULong? = null
    private var decryptSeq = ByteArray(0)
    private val aesCipher = Cipher.getInstance("AES/ECB/NoPadding").apply {
        init(Cipher.ENCRYPT_MODE, SecretKeySpec(key.copyOf(), "AES"))
    }

    fun crypt(bytes: ByteArray): ByteArray {
        val payload = ByteArray(bytes.size + 4)
        System.arraycopy(bytes, 0, payload, 0, bytes.size)
        writeUInt32(payload, bytes.size, checksum(bytes))
        encryptSeq = expandCryptSeq(encryptSeq, payload.size, encryptNonce)
        val encryptedPayload = doXor(payload, encryptSeq)
        return encryptNonceBytes + encryptedPayload
    }

    fun decrypt(bytes: ByteArray): ByteArray? {
        if (bytes.size < 9) {
            return null
        }

        val nonce = readUInt64(bytes, 0)
        if (decryptNonce != nonce) {
            decryptNonce = nonce
            decryptSeq = ByteArray(0)
        }

        val encrypted = bytes.copyOfRange(8, bytes.size)
        decryptSeq = expandCryptSeq(decryptSeq, encrypted.size, nonce)
        val decrypted = doXor(encrypted, decryptSeq)
        if (decrypted.size < 4) {
            return null
        }

        val storedChecksum = readUInt32(decrypted, decrypted.size - 4)
        val plain = decrypted.copyOfRange(0, decrypted.size - 4)
        if (checksum(plain) != storedChecksum) {
            return null
        }

        return plain
    }

    private fun expandCryptSeq(currentSeq: ByteArray, requiredLen: Int, nonce: ULong): ByteArray {
        if (requiredLen <= currentSeq.size) {
            return currentSeq
        }

        val chunksCount = (requiredLen + 15) / 16
        val existingChunks = currentSeq.size / 16
        val seq = currentSeq.copyOf(chunksCount * 16)
        for (chunk in existingChunks until chunksCount) {
            val first = nonce + chunk.toULong()
            val second = nonce + (chunk + 1).toULong()
            val block = ByteBuffer.allocate(16)
                .order(ByteOrder.BIG_ENDIAN)
                .putLong(first.toLong())
                .putLong(second.toLong())
                .array()
            val encryptedBlock = aesCipher.doFinal(block)
            System.arraycopy(encryptedBlock, 0, seq, chunk * 16, 16)
        }
        return seq
    }

    companion object {
        fun checksum(bytes: ByteArray): UInt {
            var sum = 0UL
            for (value in bytes) {
                sum += value.toUByte().toULong()
            }
            return (sum and 0xFFFF_FFFFu).toUInt()
        }

        fun doXor(bytes: ByteArray, cryptSeq: ByteArray): ByteArray {
            val result = ByteArray(bytes.size)
            for (i in bytes.indices) {
                result[i] = (bytes[i].toInt() xor cryptSeq[i].toInt()).toByte()
            }
            return result
        }

        private fun writeUInt32(target: ByteArray, offset: Int, value: UInt) {
            target[offset] = ((value.toLong() ushr 24) and 0xFF).toByte()
            target[offset + 1] = ((value.toLong() ushr 16) and 0xFF).toByte()
            target[offset + 2] = ((value.toLong() ushr 8) and 0xFF).toByte()
            target[offset + 3] = (value.toLong() and 0xFF).toByte()
        }

        private fun readUInt32(source: ByteArray, offset: Int): UInt {
            val a = source[offset].toUByte().toUInt() shl 24
            val b = source[offset + 1].toUByte().toUInt() shl 16
            val c = source[offset + 2].toUByte().toUInt() shl 8
            val d = source[offset + 3].toUByte().toUInt()
            return a or b or c or d
        }

        private fun readUInt64(source: ByteArray, offset: Int): ULong {
            var value = 0UL
            for (i in 0 until 8) {
                value = (value shl 8) or source[offset + i].toUByte().toULong()
            }
            return value
        }
    }
}
