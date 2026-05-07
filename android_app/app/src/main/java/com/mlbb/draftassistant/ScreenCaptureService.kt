package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.IBinder
import android.util.Base64
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
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

    // التعديل: نحتفظ بالنص بدلاً من الصورة لمنع الانهيار (Crash)
    @Volatile
    private var latestBase64Image: String? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // التعديل: تحديد نوع الخدمة صراحة لتعمل على Android 14 بدون انهيار
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, createNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(NOTIFICATION_ID, createNotification())
        }

        val resultCode = MainActivity.projectionResultCode
        val data = MainActivity.projectionData

        if (resultCode != -1 && data != null) {
            startCapturing(resultCode, data)
            startPeriodicCaptureAndApiCall()
        }
        return START_STICKY
    }

    private fun startCapturing(resultCode: Int, data: Intent) {
        val mediaProjectionManager = getSystemService(MediaProjectionManager::class.java)
        mediaProjection = mediaProjectionManager.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(mediaProjectionCallback, null)

        val metrics = resources.displayMetrics
        // تصغير الدقة قليلاً لتسريع الإرسال وتقليل استهلاك الإنترنت
        screenWidth = metrics.widthPixels / 2
        screenHeight = metrics.heightPixels / 2
        screenDensity = metrics.densityDpi

        setupImageReader()
        createVirtualDisplay()
        startImageReaderListener()
    }

    private fun setupImageReader() {
        imageReader = ImageReader.newInstance(screenWidth, screenHeight, PixelFormat.RGBA_8888, 2)
    }

    private fun createVirtualDisplay() {
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            VIRTUAL_DISPLAY_NAME, screenWidth, screenHeight, screenDensity,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )
    }

    private fun startImageReaderListener() {
        imageReader?.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                val bitmap = imageToBitmap(image)
                if (bitmap != null) {
                    // التعديل: نقوم بتحويل الصورة فوراً ثم ندمر الـ Bitmap
                    latestBase64Image = bitmapToBase64(bitmap)
                    bitmap.recycle() 
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
                val base64 = latestBase64Image ?: continue

                try {
                    val jsonBody = JSONObject().apply {
                        put("screenshot_b64", base64)
                    }.toString()

                    val requestBody = jsonBody.toRequestBody(mediaType)
                    val request = Request.Builder().url(API_URL).post(requestBody).build()
                    val response = okHttpClient.newCall(request).execute()

                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        if (responseBody != null) {
                            val jsonResponse = JSONObject(responseBody)
                            val winProbability = jsonResponse.optDouble("win_probability", 0.0)
                            val recommendations = jsonResponse.optString("recommendations", "{}")
                            
                            // تحديث الواجهة الشفافة
                            DraftUpdateManager.notifyUpdate(winProbability * 100, recommendations)
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "API call error: ${e.message}")
                }
            }
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val stream = ByteArrayOutputStream()
        // رفع الضغط لـ 50 لتسريع الرفع للسيرفر بشكل كبير (70 كبيرة نسبياً)
        bitmap.compress(Bitmap.CompressFormat.JPEG, 50, stream)
        return Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)
    }

    private fun imageToBitmap(image: android.media.Image): Bitmap? {
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
        return bitmap
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "Screen Capture", NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Capture Active")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .build()
    }

    private fun stopCapture() {
        virtualDisplay?.release()
        mediaProjection?.stop()
        imageReader?.close()
    }

    private val mediaProjectionCallback = object : MediaProjection.Callback() {
        override fun onStop() { stopCapture() }
    }

    override fun onDestroy() {
        serviceScope.cancel()
        stopCapture()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}