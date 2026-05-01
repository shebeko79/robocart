package com.robocart.domain.connection

import kotlinx.coroutines.flow.Flow

class ObserveRelayConnectionUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke(): Flow<Boolean> = repository.isRelayConnection
}
