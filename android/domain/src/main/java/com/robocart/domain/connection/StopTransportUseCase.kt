package com.robocart.domain.connection

class StopTransportUseCase(
    private val repository: RobotTransportRepository,
) {
    suspend operator fun invoke() {
        repository.stop()
    }
}
