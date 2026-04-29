package com.robocart.domain.connection

import kotlinx.coroutines.flow.Flow

class ObserveConnectionStateUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke(): Flow<Boolean> = repository.isConnected
}
