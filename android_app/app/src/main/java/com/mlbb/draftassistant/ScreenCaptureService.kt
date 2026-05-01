package com.mlbb.draftassistant

import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import kotlinx.coroutines.*

class ScreenCaptureService : Service() {

    companion object {
        private const val TAG = "MLBBScreenCapture"
        private const val VIRTUAL_DISPLAY_NAME = "MLBB_ScreenCapture"
        private const val SCREEN_CAPTURE_INTERVAL = 1000L
    }

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var mediaProjectionManager: MediaProjectionManager? = null

    private val serviceScope = CoroutineScope(Dispatchers.IO + Job())
    private val handler = Handler(Looper.getMainLooper())

    private var screenWidth = 0
    private var screenHeight = 0
    private var screenDensity = 0

    @Volatile
    private var latestBitmap: Bitmap? = null

    fun startCapture(context: Context, resultCode: Int, data: Intent) {
        Log.d(TAG, "Starting screen capture")
        mediaProjectionManager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager

        mediaProjection = mediaProjectionManager?.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(mediaProjectionCallback, handler)

        screenWidth = resources.displayMetrics.widthPixels
        screenHeight = resources.displayMetrics.heightPixels
        screenDensity = resources.displayMetrics.densityDpi

        setupImageReader()
        createVirtualDisplay()

        startPeriodicCapture()
    }

    private fun setupImageReader() {
        Log.d(TAG, "Setting up image reader: ${screenWidth}x$screenHeight")
        imageReader = ImageReader.newInstance(
            screenWidth,
            screenHeight,
            PixelFormat.RGBA_8888,
            2
        )
    }

    private fun createVirtualDisplay() {
        Log.d(TAG, "Creating virtual display")
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            VIRTUAL_DISPLAY_NAME,
            screenWidth,
            screenHeight,
            screenDensity,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            handler
        )
    }

    private fun startPeriodicCapture() {
        Log.d(TAG, "Starting periodic capture every ${SCREEN_CAPTURE_INTERVAL}ms")
        serviceScope.launch {
            while (isActive) {
                captureScreen()
                delay(SCREEN_CAPTURE_INTERVAL)
            }
        }
    }

    private suspend fun captureScreen() {
        withContext(Dispatchers.IO) {
            try {
                val image = imageReader?.acquireLatestImage()
                image?.let {
                    val bitmap = imageToBitmap(it)
                    it.close()

                    if (bitmap != null) {
                        latestBitmap = bitmap
                        processScreenshot(bitmap)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error capturing screen: ${e.message}")
            }
        }
    }

    private fun imageToBitmap(image: android.media.Image): Bitmap? {
        return try {
            val planes = image.planes
            val buffer = planes[0].buffer
            val pixelStride = planes[0].pixelStride
            val rowStride = planes[0].rowStride
            val rowPadding = rowStride - pixelStride * image.width

            val bitmap = Bitmap.createBitmap(
                image.width + rowPadding / pixelStride,
                image.height,
                Bitmap.Config.ARGB_8888
            )
            bitmap.copyPixelsFromBuffer(buffer)
            bitmap
        } catch (e: Exception) {
            Log.e(TAG, "Error converting image to bitmap: ${e.message}")
            null
        }
    }

    private fun processScreenshot(bitmap: Bitmap) {
        Log.d(TAG, "Processing screenshot")
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, stream)
        val byteArray = stream.toByteArray()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val apiClient = ApiClient()
                val draftState = apiClient.analyzeScreenshot(byteArray)
                Log.d(TAG, "Draft state: $draftState")
            } catch (e: Exception) {
                Log.e(TAG, "Error processing screenshot: ${e.message}")
            }
        }
    }

    fun stopCapture() {
        Log.d(TAG, "Stopping screen capture")
        serviceScope.cancel()
        virtualDisplay?.release()
        mediaProjection?.stop()
        imageReader?.close()
        latestBitmap = null
    }

    fun getLatestBitmap(): Bitmap? = latestBitmap

    private val mediaProjectionCallback = object : MediaProjection.Callback() {
        override fun onStop() {
            Log.d(TAG, "MediaProjection stopped")
            stopCapture()
            super.onStop()
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        Log.d(TAG, "ScreenCaptureService destroyed")
        super.onDestroy()
        stopCapture()
    }
}
