package com.robocart.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.robocart.data.network.RobotTransportRepositoryImpl
import com.robocart.domain.connection.ObserveConnectionStateUseCase
import com.robocart.domain.connection.ObserveIncomingJpegUseCase
import com.robocart.domain.connection.ObserveIncomingJsonUseCase
import com.robocart.domain.connection.SendJsonCommandUseCase
import com.robocart.domain.connection.StartTransportUseCase
import com.robocart.domain.connection.StopTransportUseCase
import com.robocart.presentation.MainScreen
import com.robocart.presentation.MainViewModel
import com.robocart.presentation.RobocartTheme

class MainActivity : ComponentActivity() {
    private val viewModel by viewModels<MainViewModel> {
        val repository = RobotTransportRepositoryImpl(
            hostName = "robocart.local",
            port = 5005,
        )
        MainViewModel.Factory(
            observeIncomingJson = ObserveIncomingJsonUseCase(repository),
            observeIncomingJpeg = ObserveIncomingJpegUseCase(repository),
            observeConnectionState = ObserveConnectionStateUseCase(repository),
            sendJsonCommand = SendJsonCommandUseCase(repository),
            startTransport = StartTransportUseCase(repository),
            stopTransport = StopTransportUseCase(repository),
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
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
}
