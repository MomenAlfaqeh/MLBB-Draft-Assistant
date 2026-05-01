package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*

class OverlayService : Service() {

    companion object {
        private const val CHANNEL_ID = "MLBBOverlayChannel"
        private const val NOTIFICATION_ID = 1
    }

    private lateinit var windowManager: WindowManager
    private lateinit var overlayView: View
    private var initialX: Int = 0
    private var initialY: Int = 0
    private var initialTouchX: Float = 0f
    private var initialTouchY: Float = 0f

    private val serviceScope = CoroutineScope(Dispatchers.Main + Job())
    private lateinit var apiClient: ApiClient
    private var screenCaptureService: ScreenCaptureService? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        setupOverlay()
        apiClient = ApiClient()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)

        val resultCode = intent?.getIntExtra("resultCode", -1) ?: -1
        val data = intent?.getParcelableExtra<Intent>("data")

        if (resultCode != -1 && data != null) {
            startScreenCapture(resultCode, data)
        }

        startRecommendationUpdates()

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "MLBB Overlay Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows MLBB draft recommendations"
            }
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Draft Assistant")
            .setContentText("Overlay is active")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun setupOverlay() {
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager

        overlayView = LayoutInflater.from(this).inflate(R.layout.overlay_layout, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = 0
            y = 100
        }

        setupDragListener(params)
        windowManager.addView(overlayView, params)
    }

    private fun setupDragListener(params: WindowManager.LayoutParams) {
        overlayView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    params.x = initialX + (event.rawX - initialTouchX).toInt()
                    params.y = initialY + (event.rawY - initialTouchY).toInt()
                    windowManager.updateViewLayout(overlayView, params)
                    true
                }
                else -> false
            }
        }
    }

    private fun startScreenCapture(resultCode: Int, data: Intent) {
        screenCaptureService = ScreenCaptureService().apply {
            startCapture(this@OverlayService, resultCode, data)
        }
    }

    private fun startRecommendationUpdates() {
        serviceScope.launch {
            while (isActive) {
                updateRecommendations()
                delay(1000)
            }
        }
    }

    private suspend fun updateRecommendations() {
        withContext(Dispatchers.IO) {
            try {
                val recommendations = apiClient.getRecommendations()
                withContext(Dispatchers.Main) {
                    updateOverlayUI(recommendations)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun updateOverlayUI(recommendations: List<Recommendation>) {
        val laneText = overlayView.findViewById<TextView>(R.id.tv_lane_recommendations)
        val winRateText = overlayView.findViewById<TextView>(R.id.tv_win_probability)

        if (recommendations.isNotEmpty()) {
            val laneRecs = recommendations.joinToString("\n") {
                "${it.hero}: ${it.lane} (${it.confidence}%)"
            }
            laneText.text = laneRecs

            val avgWinRate = recommendations.map { it.winRate }.average()
            winRateText.text = "Win Probability: ${String.format("%.1f", avgWinRate)}%"
        } else {
            laneText.text = "Analyzing draft..."
            winRateText.text = "Win Probability: --%"
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
        screenCaptureService?.stopCapture()
        if (::windowManager.isInitialized && ::overlayView.isInitialized) {
            windowManager.removeView(overlayView)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

data class Recommendation(
    val hero: String,
    val lane: String,
    val confidence: Int,
    val winRate: Double
)
