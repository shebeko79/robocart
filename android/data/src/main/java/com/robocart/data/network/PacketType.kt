package com.robocart.data.network

enum class PacketType(val wireValue: Int) {
    JSON(0),
    JPG(1),
    ACK(2),
    ;

    companion object {
        fun fromWireValue(value: Int): PacketType? = entries.firstOrNull { it.wireValue == value }
    }
}
