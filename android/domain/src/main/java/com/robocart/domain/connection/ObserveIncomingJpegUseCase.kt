package com.robocart.domain.connection

import kotlinx.coroutines.flow.Flow

class ObserveIncomingJpegUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke(): Flow<ByteArray> = repository.jpegEvents
}
