package com.robocart.domain.connection

import kotlinx.coroutines.flow.Flow

class ObserveIncomingJsonUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke(): Flow<Any?> = repository.jsonEvents
}
