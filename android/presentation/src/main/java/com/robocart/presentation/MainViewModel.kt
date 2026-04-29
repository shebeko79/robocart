package com.robocart.presentation

import android.graphics.BitmapFactory
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.asImageBitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.robocart.domain.connection.ObserveConnectionStateUseCase
import com.robocart.domain.connection.ObserveIncomingJpegUseCase
import com.robocart.domain.connection.ObserveIncomingJsonUseCase
import com.robocart.domain.connection.SendJsonCommandUseCase
import com.robocart.domain.connection.StartTransportUseCase
import com.robocart.domain.connection.StopTransportUseCase
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.PI

class MainViewModel(
    private val observeIncomingJson: ObserveIncomingJsonUseCase,
    private val observeIncomingJpeg: ObserveIncomingJpegUseCase,
    private val observeConnectionState: ObserveConnectionStateUseCase,
    private val sendJsonCommand: SendJsonCommandUseCase,
    private val startTransport: StartTransportUseCase,
    private val stopTransport: StopTransportUseCase,
) : ViewModel() {
    var uiState by mutableStateOf(MainScreenState())
        private set

    private var currentStateName: String = "unknown"

    init {
        viewModelScope.launch {
            observeConnectionState().collect { isConnected ->
                uiState = uiState.copy(isConnected = isConnected)
            }
        }
        viewModelScope.launch {
            observeIncomingJson().collect(::onJsonPayload)
        }
        viewModelScope.launch {
            observeIncomingJpeg().collect(::onJpegPayload)
        }
    }

    fun onStart() {
        startTransport()
    }

    fun onStop() {
        viewModelScope.launch {
            stopTransport()
        }
    }

    fun onControlAction(action: MainControlAction) {
        val cmd = when (action) {
            MainControlAction.CameraUp -> mapOf("cmd" to "move_cam", "pan" to 0.0, "tilt" to -CAM_ANG)
            MainControlAction.CameraDown -> mapOf("cmd" to "move_cam", "pan" to 0.0, "tilt" to CAM_ANG)
            MainControlAction.CameraLeft -> mapOf("cmd" to "move_cam", "pan" to -CAM_ANG, "tilt" to 0.0)
            MainControlAction.CameraRight -> mapOf("cmd" to "move_cam", "pan" to CAM_ANG, "tilt" to 0.0)
            MainControlAction.CameraLeftPreset -> mapOf("cmd" to "moveto_cam", "pan" to "LEFT", "tilt" to "FRONT")
            MainControlAction.CameraRightPreset -> mapOf("cmd" to "moveto_cam", "pan" to "RIGHT", "tilt" to "FRONT")
            MainControlAction.CameraFrontPreset -> mapOf("cmd" to "moveto_cam", "pan" to "CENTER", "tilt" to "FRONT")
            MainControlAction.CameraTopPreset -> mapOf("cmd" to "moveto_cam", "pan" to "CENTER", "tilt" to "UP")
            MainControlAction.CameraBackPreset -> mapOf("cmd" to "moveto_cam", "pan" to "CENTER", "tilt" to "BACKWARD")
            MainControlAction.CameraLeftMostPreset -> mapOf("cmd" to "moveto_cam", "pan" to "MIN", "tilt" to "CURRENT")
            MainControlAction.CameraRightMostPreset -> mapOf("cmd" to "moveto_cam", "pan" to "MAX", "tilt" to "CURRENT")
            MainControlAction.CameraBackMostPreset -> mapOf("cmd" to "moveto_cam", "pan" to "CURRENT", "tilt" to "MIN")
            MainControlAction.CameraFrontMostPreset -> mapOf("cmd" to "moveto_cam", "pan" to "CURRENT", "tilt" to "MAX")
            MainControlAction.CameraRelease -> mapOf("cmd" to "release_cam")
            MainControlAction.CartForward -> mapOf("cmd" to "move", "speed" to 1.0, "pan" to 0.0)
            MainControlAction.CartBackward -> mapOf("cmd" to "move", "speed" to -1.0, "pan" to 0.0)
            MainControlAction.CartLeft -> mapOf("cmd" to "move", "speed" to 0.0, "pan" to -1.0)
            MainControlAction.CartRight -> mapOf("cmd" to "move", "speed" to 0.0, "pan" to 1.0)
        }
        sendJsonCommand(cmd)
    }

    fun onDynamicActionClick(caption: String) {
        sendJsonCommand(
            mapOf(
                "cmd" to "click",
                "state_name" to currentStateName,
                "caption" to caption,
            )
        )
    }

    fun onImageClick(x: Float, y: Float) {
        sendJsonCommand(
            mapOf(
                "cmd" to "click_point",
                "state_name" to currentStateName,
                "x" to x.toDouble(),
                "y" to y.toDouble(),
            )
        )
    }

    fun onImageRectangle(x1: Float, y1: Float, x2: Float, y2: Float) {
        sendJsonCommand(
            mapOf(
                "cmd" to "sel_rect",
                "state_name" to currentStateName,
                "x1" to x1.toDouble(),
                "y1" to y1.toDouble(),
                "x2" to x2.toDouble(),
                "y2" to y2.toDouble(),
            )
        )
    }

    private fun onJsonPayload(payload: Any?) {
        val json = payload as? JSONObject ?: return
        val stateName = json.optString("state_name", currentStateName)
        val acceptClick = json.optBoolean("accept_click", false)
        val acceptRectangle = json.optBoolean("accept_rectangle", false)
        val message = when {
            acceptClick -> json.optString("click_cap", "")
            acceptRectangle -> json.optString("rectangle_cap", "")
            else -> json.optString("message", "No message")
        }
        val voltageValue = json.optDouble("voltage")
        val voltageText = if (voltageValue.isNaN()) "--.-V" else "%.1fV".format(voltageValue)

        currentStateName = stateName
        uiState = uiState.copy(
            stateName = stateName,
            message = message,
            voltageText = voltageText,
            dynamicButtons = json.optJSONArray("buttons").toDynamicButtons(),
            acceptClick = acceptClick,
            acceptRectangle = acceptRectangle,
        )
    }

    private fun onJpegPayload(payload: ByteArray) {
        val bitmap = BitmapFactory.decodeByteArray(payload, 0, payload.size) ?: return
        uiState = uiState.copy(frame = bitmap.asImageBitmap())
    }

    private fun JSONArray?.toDynamicButtons(): List<DynamicActionButton> {
        if (this == null) {
            return emptyList()
        }
        return buildList {
            for (index in 0 until length()) {
                val item = optJSONObject(index) ?: continue
                add(
                    DynamicActionButton(
                        caption = item.optString("caption"),
                        enabled = item.optBoolean("enabled", true),
                    )
                )
            }
        }
    }

    private companion object {
        const val CAM_ANG = 5.0 / 180.0 * PI
    }

    class Factory(
        private val observeIncomingJson: ObserveIncomingJsonUseCase,
        private val observeIncomingJpeg: ObserveIncomingJpegUseCase,
        private val observeConnectionState: ObserveConnectionStateUseCase,
        private val sendJsonCommand: SendJsonCommandUseCase,
        private val startTransport: StartTransportUseCase,
        private val stopTransport: StopTransportUseCase,
    ) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            require(modelClass == MainViewModel::class.java) {
                "Unsupported modelClass: ${modelClass.name}"
            }
            return MainViewModel(
                observeIncomingJson = observeIncomingJson,
                observeIncomingJpeg = observeIncomingJpeg,
                observeConnectionState = observeConnectionState,
                sendJsonCommand = sendJsonCommand,
                startTransport = startTransport,
                stopTransport = stopTransport,
            ) as T
        }
    }
}
