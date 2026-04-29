package com.robocart.domain.connection

class StartTransportUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke() {
        repository.start()
    }
}
