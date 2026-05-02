package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.IBinder
import android.util.Log

class ScreenCaptureService : Service() {

    companion object {
        private const val TAG = "MLBBScreenCapture"
        private const val CHANNEL_ID = "MLBBOverlayChannel"
        private const val NOTIFICATION_ID = 2
        private const val VIRTUAL_DISPLAY_NAME = "MLBB_ScreenCapture"
    }

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null

    private var screenWidth = 0
    private var screenHeight = 0
    private var screenDensity = 0

    @Volatile private var latestBitmap: Bitmap? = null

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "ScreenCaptureService created")
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "ScreenCaptureService started")
        startForeground(NOTIFICATION_ID, createNotification())

        val resultCode = intent?.getIntExtra("resultCode", -1) ?: -1
        val data = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent?.getParcelableExtra("data", Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent?.getParcelableExtra<Intent>("data")
        }

        if (resultCode != -1 && data != null) {
            Log.d(TAG, "Creating MediaProjection with resultCode=$resultCode")
            startCapturing(resultCode, data)
        }

        return START_STICKY
    }

    private fun startCapturing(resultCode: Int, data: Intent) {
        val mediaProjectionManager = getSystemService(MediaProjectionManager::class.java)
        mediaProjection = mediaProjectionManager.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(mediaProjectionCallback, null)

        val metrics = resources.displayMetrics
        screenWidth = metrics.widthPixels
        screenHeight = metrics.heightPixels
        screenDensity = metrics.densityDpi

        Log.d(TAG, "Screen: ${screenWidth}x${screenHeight} @ ${screenDensity}dpi")
        setupImageReader()
        createVirtualDisplay()
        startImageReaderListener()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "MLBB Screen Capture",
                NotificationManager.IMPORTANCE_LOW
            ).apply { description = "Captures screen for draft analysis" }
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification =
        androidx.core.app.NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Screen Capture")
            .setContentText("Capturing screen...")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(androidx.core.app.NotificationCompat.PRIORITY_LOW)
            .build()

    private fun setupImageReader() {
        imageReader = ImageReader.newInstance(screenWidth, screenHeight, PixelFormat.RGBA_8888, 2)
    }

    private fun createVirtualDisplay() {
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            VIRTUAL_DISPLAY_NAME,
            screenWidth,
            screenHeight,
            screenDensity,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            null
        )
    }

    private fun startImageReaderListener() {
        imageReader?.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                val bitmap = imageToBitmap(image)
                if (bitmap != null) {
                    latestBitmap?.recycle()
                    latestBitmap = bitmap
                    ScreenCaptureRepository.updateBitmap(bitmap)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Image listener error: ${e.message}")
            } finally {
                image.close()
            }
        }, null)
    }

    fun getLatestBitmap(): Bitmap? = latestBitmap?.copy(latestBitmap!!.config!!, false)

    private fun imageToBitmap(image: android.media.Image): Bitmap? {
        return try {
            val plane = image.planes[0]
            val pixelStride = plane.pixelStride
            val rowStride = plane.rowStride
            val rowPadding = rowStride - pixelStride * image.width
            val bitmap = Bitmap.createBitmap(
                image.width + rowPadding / pixelStride,
                image.height,
                Bitmap.Config.ARGB_8888
            )
            bitmap.copyPixelsFromBuffer(plane.buffer)
            bitmap
        } catch (e: Exception) {
            Log.e(TAG, "Bitmap conversion error: ${e.message}")
            null
        }
    }

    fun stopCapture() {
        Log.d(TAG, "Stopping screen capture")
        latestBitmap?.recycle()
        latestBitmap = null
        virtualDisplay?.release()
        mediaProjection?.stop()
        imageReader?.close()
    }

    private val mediaProjectionCallback = object : MediaProjection.Callback() {
        override fun onStop() {
            Log.d(TAG, "MediaProjection stopped externally")
            stopCapture()
        }
    }

    override fun onDestroy() {
        Log.d(TAG, "ScreenCaptureService destroyed")
        stopCapture()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
