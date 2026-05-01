package com.robocart.app

import android.os.Bundle
import android.util.Log
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.robocart.data.network.RobotTransportRepositoryImpl
import com.robocart.domain.connection.ObserveConnectionStateUseCase
import com.robocart.domain.connection.ObserveIncomingJpegUseCase
import com.robocart.domain.connection.ObserveIncomingJsonUseCase
import com.robocart.domain.connection.ObserveRelayConnectionUseCase
import com.robocart.domain.connection.SendJsonCommandUseCase
import com.robocart.domain.connection.StartTransportUseCase
import com.robocart.domain.connection.StopTransportUseCase
import com.robocart.presentation.MainScreen
import com.robocart.presentation.MainViewModel
import com.robocart.presentation.RobocartTheme

class MainActivity : ComponentActivity() {
    private companion object {
        const val TAG = "MainActivity"
        const val UDP_KEY_FILE_NAME = "udp.key"
        const val AES_KEY_SIZE_BYTES = 16
    }

    private val viewModel by viewModels<MainViewModel> {
        val repository = RobotTransportRepositoryImpl(
            context = applicationContext,
            port = 5005,
            key = loadUdpKeyFromAssets(),
        )
        MainViewModel.Factory(
            observeIncomingJson = ObserveIncomingJsonUseCase(repository),
            observeIncomingJpeg = ObserveIncomingJpegUseCase(repository),
            observeConnectionState = ObserveConnectionStateUseCase(repository),
            observeRelayConnection = ObserveRelayConnectionUseCase(repository),
            sendJsonCommand = SendJsonCommandUseCase(repository),
            startTransport = StartTransportUseCase(repository),
            stopTransport = StopTransportUseCase(repository),
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContent {
            RobocartTheme {
                MainScreen(
                    state = viewModel.uiState,
                    onControlAction = viewModel::onControlAction,
                    onDynamicActionClick = viewModel::onDynamicActionClick,
                    onImageClick = viewModel::onImageClick,
                    onImageRectangle = viewModel::onImageRectangle,
                )
            }
        }
    }

    override fun onStart() {
        super.onStart()
        viewModel.onStart()
    }

    override fun onStop() {
        viewModel.onStop()
        super.onStop()
    }

    private fun loadUdpKeyFromAssets(): ByteArray? {
        val keyBytes = runCatching {
            applicationContext.assets.open(UDP_KEY_FILE_NAME).use { it.readBytes() }
        }.getOrElse { error ->
            Log.i(TAG, "UDP key is not bundled in assets: ${error.message}")
            return null
        }
        if (keyBytes.size != AES_KEY_SIZE_BYTES) {
            Log.w(TAG, "Ignoring udp.key with invalid size=${keyBytes.size}, expected=$AES_KEY_SIZE_BYTES")
            return null
        }
        return keyBytes
    }
}
