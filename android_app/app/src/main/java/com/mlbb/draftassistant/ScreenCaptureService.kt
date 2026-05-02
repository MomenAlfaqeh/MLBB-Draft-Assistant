package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import androidx.core.app.NotificationCompat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.IBinder
import android.util.Base64
import android.util.Log
import kotlinx.coroutines.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayOutputStream

class ScreenCaptureService : Service() {

    companion object {
        private const val TAG = "MLBBScreenCapture"
        private const val CHANNEL_ID = "MLBBOverlayChannel"
        private const val NOTIFICATION_ID = 2
        private const val VIRTUAL_DISPLAY_NAME = "MLBB_ScreenCapture"
        private const val CAPTURE_INTERVAL_MS = 1000L
        private const val API_URL = "https://mlbb-draft-assistant-g19m.onrender.com/analyze"
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val okHttpClient = OkHttpClient()
    private val mediaType = "application/json".toMediaType()

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null

    private var screenWidth = 0
    private var screenHeight = 0
    private var screenDensity = 0

    @Volatile
    private var latestBitmap: Bitmap? = null

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "ScreenCaptureService created")
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "ScreenCaptureService started")
        startForeground(NOTIFICATION_ID, createNotification())

        Toast.makeText(this, "ScreenCaptureService started!", Toast.LENGTH_SHORT).show()

        DraftUpdateManager.notifyUpdate(55.0, """{"EXP":[],"Jungle":[],"Mid":[],"Gold":[],"Roam":[]}""")
        Toast.makeText(this, "Test: Win=55% should appear now", Toast.LENGTH_SHORT).show()
        Log.d(TAG, "Test update sent - win_probability=55.0")

        val resultCode = intent?.getIntExtra("resultCode", -1) ?: -1
        val data = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent?.getParcelableExtra("data", Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent?.getParcelableExtra<Intent>("data")
        }

        if (resultCode != -1 && data != null) {
            startCapturing(resultCode, data)
            startPeriodicCaptureAndApiCall()
        } else {
            Log.w(TAG, "No valid projection data received - resultCode=$resultCode, data=$data")
        }

        return START_STICKY
    }

    private fun startCapturing(resultCode: Int, data: Intent) {
        val mediaProjectionManager = getSystemService(MediaProjectionManager::class.java)
        mediaProjection = mediaProjectionManager.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(mediaProjectionCallback, null)
        Log.d(TAG, "MediaProjection created")

        val metrics = resources.displayMetrics
        screenWidth = metrics.widthPixels
        screenHeight = metrics.heightPixels
        screenDensity = metrics.densityDpi

        Log.d(TAG, "Screen: ${screenWidth}x${screenHeight} @ ${screenDensity}dpi")
        setupImageReader()
        createVirtualDisplay()
        startImageReaderListener()
    }

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
                    Log.d(TAG, "Screenshot captured, size: ${bitmap.byteCount} bytes")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Image listener error: ${e.message}")
            } finally {
                image.close()
            }
        }, null)
    }

    private fun startPeriodicCaptureAndApiCall() {
        serviceScope.launch {
            while (isActive) {
                delay(CAPTURE_INTERVAL_MS)
                val bitmap = latestBitmap ?: continue
                val base64 = bitmapToBase64(bitmap)
                if (base64.isEmpty()) continue

                try {
                    Log.d(TAG, "Sending to API...")
                    val jsonBody = JSONObject().apply {
                        put("screenshot_b64", base64)
                    }.toString()
                    val requestBody = jsonBody.toRequestBody(mediaType)
                    val request = Request.Builder()
                        .url(API_URL)
                        .post(requestBody)
                        .build()

                    val response = okHttpClient.newCall(request).execute()
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        Log.d(TAG, "API response: $responseBody")
                        if (responseBody != null) {
                            val jsonResponse = JSONObject(responseBody)
                            val winProbability = jsonResponse.optDouble("win_probability", 0.0)
                            val recommendations = jsonResponse.optString("recommendations", "{}")

                            DraftUpdateManager.notifyUpdate(winProbability * 100, recommendations)
                            Log.d(TAG, "DraftUpdateManager notified - win_probability=${winProbability * 100}")
                        }
                    } else {
                        Log.e(TAG, "API call failed: ${response.code} ${response.message}")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error during capture/API call: ${e.message}")
                }
            }
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        return try {
            val stream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 70, stream)
            Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)
        } catch (e: Exception) {
            Log.e(TAG, "Base64 conversion error: ${e.message}")
            ""
        }
    }

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

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Screen Capture")
            .setContentText("Capturing screen...")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun stopCapture() {
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
        serviceScope.cancel()
        stopCapture()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
