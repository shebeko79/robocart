package com.robocart.domain.connection

import kotlinx.coroutines.flow.Flow

interface RobotTransportRepository {
    val jsonEvents: Flow<Any?>
    val jpegEvents: Flow<ByteArray>
    val isConnected: Flow<Boolean>
    val isRelayConnection: Flow<Boolean>

    fun start()
    suspend fun stop()
    fun sendJson(payload: Map<String, Any?>)
}
