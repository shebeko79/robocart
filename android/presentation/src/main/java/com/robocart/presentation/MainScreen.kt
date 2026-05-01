package com.robocart.presentation

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import kotlin.math.abs
import kotlin.math.max

data class DynamicActionButton(
    val caption: String,
    val enabled: Boolean = true
)

data class MainScreenState(
    val frame: ImageBitmap? = null,
    val isConnected: Boolean = false,
    val isRelayConnection: Boolean = false,
    val stateName: String = "unknown",
    val message: String = "No message",
    val voltageText: String = "--.-V",
    val latencyText: String = "-- s",
    val dynamicButtons: List<DynamicActionButton> = emptyList(),
    val acceptClick: Boolean = false,
    val acceptRectangle: Boolean = false,
)

enum class MainControlAction {
    CameraUp,
    CameraDown,
    CameraLeft,
    CameraRight,
    CameraLeftPreset,
    CameraRightPreset,
    CameraFrontPreset,
    CameraTopPreset,
    CameraBackPreset,
    CameraLeftMostPreset,
    CameraRightMostPreset,
    CameraBackMostPreset,
    CameraFrontMostPreset,
    CameraRelease,
    CartForward,
    CartBackward,
    CartLeft,
    CartRight,
}

@Composable
fun MainScreen(
    state: MainScreenState = MainScreenState(),
    onControlAction: (MainControlAction) -> Unit = {},
    onDynamicActionClick: (String) -> Unit = {},
    onImageClick: (Float, Float) -> Unit = { _, _ -> },
    onImageRectangle: (Float, Float, Float, Float) -> Unit = { _, _, _, _ -> },
) {
    val configuration = LocalConfiguration.current
    val isLandscape = configuration.orientation == Configuration.ORIENTATION_LANDSCAPE

    Surface(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (isLandscape) {
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxSize()
                ) {
                    VideoPanel(
                        state = state,
                        onImageClick = onImageClick,
                        onImageRectangle = onImageRectangle,
                        modifier = Modifier
                            .weight(1.4f)
                            .fillMaxSize()
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    ControlsPanel(
                        state = state,
                        onControlAction = onControlAction,
                        onDynamicActionClick = onDynamicActionClick,
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxSize()
                    )
                }
            } else {
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    VideoPanel(
                        state = state,
                        onImageClick = onImageClick,
                        onImageRectangle = onImageRectangle,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f, fill = false)
                    )
                    ControlsPanel(
                        state = state,
                        onControlAction = onControlAction,
                        onDynamicActionClick = onDynamicActionClick,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f)
                    )
                }
            }
            StatusLine(state = state)
        }
    }
}

@Composable
private fun VideoPanel(
    state: MainScreenState,
    onImageClick: (Float, Float) -> Unit,
    onImageRectangle: (Float, Float, Float, Float) -> Unit,
    modifier: Modifier = Modifier
) {
    var boxSize by remember { mutableStateOf(IntSize.Zero) }
    var dragStart by remember { mutableStateOf<Offset?>(null) }
    var dragEnd by remember { mutableStateOf<Offset?>(null) }

    Column(modifier = modifier) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                .onSizeChanged { boxSize = it }
                .pointerInput(state.frame, state.acceptClick, state.acceptRectangle, boxSize) {
                    awaitEachGesture {
                        val down = awaitFirstDown(requireUnconsumed = false)
                        val frame = state.frame ?: return@awaitEachGesture
                        val start = down.position
                        var hasDragged = false
                        var pointerUp = false
                        var end = start
                        var draggedDistance = 0f
                        if (state.acceptRectangle) {
                            dragStart = start
                            dragEnd = start
                        }

                        while (!pointerUp) {
                            val event = awaitPointerEvent()
                            val change = event.changes.firstOrNull { it.id == down.id } ?: continue
                            if (change.positionChanged()) {
                                end = change.position
                                draggedDistance = max(draggedDistance, (end - start).getDistance())
                                if (state.acceptRectangle) {
                                    dragEnd = end
                                }
                                if (draggedDistance > 8f) {
                                    hasDragged = true
                                }
                            }
                            if (change.changedToUp()) {
                                pointerUp = true
                            }
                        }

                        val normalizedStart = toNormalizedOffset(start, boxSize, frame) ?: run {
                            dragStart = null
                            dragEnd = null
                            return@awaitEachGesture
                        }

                        if (!hasDragged && state.acceptClick) {
                            onImageClick(normalizedStart.x, normalizedStart.y)
                        } else if (hasDragged && state.acceptRectangle) {
                            val normalizedEnd = toNormalizedOffset(end, boxSize, frame)
                            if (normalizedEnd != null &&
                                (abs(normalizedStart.x - normalizedEnd.x) > 0.001f ||
                                    abs(normalizedStart.y - normalizedEnd.y) > 0.001f)
                            ) {
                                onImageRectangle(
                                    normalizedStart.x,
                                    normalizedStart.y,
                                    normalizedEnd.x,
                                    normalizedEnd.y,
                                )
                            }
                        }

                        dragStart = null
                        dragEnd = null
                    }
                }
                .drawWithContent {
                    drawContent()
                    if (state.acceptRectangle && dragStart != null && dragEnd != null) {
                        val topLeft = Offset(
                            x = minOf(dragStart!!.x, dragEnd!!.x),
                            y = minOf(dragStart!!.y, dragEnd!!.y)
                        )
                        val rectSize = Size(
                            width = abs(dragStart!!.x - dragEnd!!.x),
                            height = abs(dragStart!!.y - dragEnd!!.y)
                        )
                        drawRect(
                            color = Color.Red.copy(alpha = 0.24f),
                            topLeft = topLeft,
                            size = rectSize
                        )
                        drawRect(
                            color = Color.Red,
                            topLeft = topLeft,
                            size = rectSize,
                            style = androidx.compose.ui.graphics.drawscope.Stroke(
                                width = 2.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(12f, 8f))
                            )
                        )
                    }
                },
            contentAlignment = Alignment.Center
        ) {
            if (state.frame != null) {
                androidx.compose.foundation.Image(
                    bitmap = state.frame,
                    contentDescription = "Video stream",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Fit
                )
            } else {
                Text(
                    text = "Waiting for video stream...",
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }
    }
}

private fun toNormalizedOffset(
    point: Offset,
    containerSize: IntSize,
    image: ImageBitmap
): Offset? {
    if (containerSize.width <= 0 || containerSize.height <= 0) {
        return null
    }
    val iw = image.width.toFloat()
    val ih = image.height.toFloat()
    if (iw <= 0f || ih <= 0f) {
        return null
    }

    val containerWidth = containerSize.width.toFloat()
    val containerHeight = containerSize.height.toFloat()
    val scale = minOf(containerWidth / iw, containerHeight / ih)
    val drawnWidth = iw * scale
    val drawnHeight = ih * scale
    val left = (containerWidth - drawnWidth) / 2f
    val top = (containerHeight - drawnHeight) / 2f

    if (point.x < left || point.x > left + drawnWidth || point.y < top || point.y > top + drawnHeight) {
        return null
    }

    val x = ((point.x - left) / drawnWidth).coerceIn(0f, 1f)
    val y = ((point.y - top) / drawnHeight).coerceIn(0f, 1f)
    return Offset(x, y)
}

@Composable
private fun StatusLine(state: MainScreenState) {
    val statusColor = when {
        !state.isConnected -> Color(0xFFFF9800)
        state.isRelayConnection -> Color(0xFF1976D2)
        else -> Color(0xFF2E7D32)
    }
    val hasMessage = state.message.isNotBlank() && state.message != "No message"

    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerHigh)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(statusColor)
            )
            Text(text = state.latencyText, style = MaterialTheme.typography.bodyMedium)
            Text(text = state.voltageText, style = MaterialTheme.typography.bodyMedium)
            Text(text = state.stateName, style = MaterialTheme.typography.bodyMedium)
            if (hasMessage) {
                Text(
                    text = state.message,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.weight(1f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Composable
private fun ControlsPanel(
    state: MainScreenState,
    onControlAction: (MainControlAction) -> Unit,
    onDynamicActionClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            ControlSection("Camera") {
                Dpad(
                    upLabel = "Up",
                    downLabel = "Down",
                    leftLabel = "Left",
                    rightLabel = "Right",
                    onUp = { onControlAction(MainControlAction.CameraUp) },
                    onDown = { onControlAction(MainControlAction.CameraDown) },
                    onLeft = { onControlAction(MainControlAction.CameraLeft) },
                    onRight = { onControlAction(MainControlAction.CameraRight) }
                )
            }
        }
        item {
            ControlSection("Camera views") {
                SimpleRowButtons(
                    "Back most" to { onControlAction(MainControlAction.CameraBackMostPreset) }
                )
                SimpleRowButtons(
                    "Back" to { onControlAction(MainControlAction.CameraBackPreset) }
                )
                SimpleRowButtons(
                    "Left most" to { onControlAction(MainControlAction.CameraLeftMostPreset) },
                    "Top" to { onControlAction(MainControlAction.CameraTopPreset) },
                    "Right most" to { onControlAction(MainControlAction.CameraRightMostPreset) }
                )
                SimpleRowButtons(
                    "Left" to { onControlAction(MainControlAction.CameraLeftPreset) },
                    "Front" to { onControlAction(MainControlAction.CameraFrontPreset) },
                    "Right" to { onControlAction(MainControlAction.CameraRightPreset) }
                )
                SimpleRowButtons(
                    "Front most" to { onControlAction(MainControlAction.CameraFrontMostPreset) },
                    "Release" to { onControlAction(MainControlAction.CameraRelease) }
                )
            }
        }
        item {
            ControlSection("Cart") {
                Dpad(
                    upLabel = "Forward",
                    downLabel = "Backward",
                    leftLabel = "Left",
                    rightLabel = "Right",
                    onUp = { onControlAction(MainControlAction.CartForward) },
                    onDown = { onControlAction(MainControlAction.CartBackward) },
                    onLeft = { onControlAction(MainControlAction.CartLeft) },
                    onRight = { onControlAction(MainControlAction.CartRight) }
                )
            }
        }
        item {
            ControlSection("Actions") {
                if (state.dynamicButtons.isEmpty()) {
                    Text(text = "No dynamic actions", style = MaterialTheme.typography.bodySmall)
                } else {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        state.dynamicButtons.forEach { button ->
                            Button(
                                onClick = { onDynamicActionClick(button.caption) },
                                enabled = button.enabled,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(text = button.caption)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ControlSection(
    title: String,
    content: @Composable () -> Unit
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainer)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleSmall)
            Spacer(modifier = Modifier.height(6.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Spacer(modifier = Modifier.height(8.dp))
            content()
        }
    }
}

@Composable
private fun Dpad(
    upLabel: String,
    downLabel: String,
    leftLabel: String,
    rightLabel: String,
    onUp: () -> Unit,
    onDown: () -> Unit,
    onLeft: () -> Unit,
    onRight: () -> Unit
) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
        Column(modifier = Modifier.fillMaxHeight(), verticalArrangement = Arrangement.Center) {
            OutlinedButton(onClick = onLeft) { Text(leftLabel) }

        }
        Column(modifier = Modifier.fillMaxHeight(), verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally) {
            OutlinedButton(onClick = onUp) { Text(upLabel) }
            OutlinedButton(onClick = onDown) { Text(downLabel) }
        }
        Column(modifier = Modifier.fillMaxHeight(), verticalArrangement = Arrangement.Center) {
            OutlinedButton(onClick = onRight) { Text(rightLabel) }
        }
    }
}

@Composable
private fun SimpleRowButtons(vararg actions: Pair<String, () -> Unit>) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        actions.forEach { (caption, action) ->
            OutlinedButton(
                onClick = action,
                modifier = Modifier.weight(1f)
            ) {
                Text(caption)
            }
        }
    }
    Spacer(modifier = Modifier.height(6.dp))
}

