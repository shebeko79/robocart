package com.robocart.domain.connection

class SendJsonCommandUseCase(
    private val repository: RobotTransportRepository,
) {
    operator fun invoke(payload: Map<String, Any?>) {
        repository.sendJson(payload)
    }
}
