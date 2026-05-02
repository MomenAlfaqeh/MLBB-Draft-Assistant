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
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.NotificationCompat

class OverlayService : Service() {

    companion object {
        private const val TAG = "MLBBOverlay"
        private const val CHANNEL_ID = "MLBBOverlayChannel"
        private const val NOTIFICATION_ID = 1
    }

    private lateinit var windowManager: WindowManager
    private lateinit var overlayView: View
    private var initialX = 0
    private var initialY = 0
    private var initialTouchX = 0f
    private var initialTouchY = 0f

    private val updateCallback: () -> Unit = {
        val winText = overlayView.findViewById<TextView>(R.id.tv_win_probability)
        val laneText = overlayView.findViewById<TextView>(R.id.tv_lane_recommendations)
        winText.text = "Win: ${DraftUpdateManager.winProbability.toInt()}%"
        laneText.text = DraftUpdateManager.recommendations
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "OverlayService created")
        createNotificationChannel()
        setupOverlay()
        DraftUpdateManager.addListener(updateCallback)
        Log.d(TAG, "DraftUpdateManager listener registered")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "OverlayService onStartCommand")
        startForeground(NOTIFICATION_ID, createNotification())

        // Small delay to ensure MainActivity has saved the data
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            val resultCode = MainActivity.projectionResultCode
            val data = MainActivity.projectionData

            Toast.makeText(this, "OverlayService: resultCode=$resultCode data=${data != null}", Toast.LENGTH_LONG).show()

            if (resultCode != -1 && data != null) {
                Toast.makeText(this, "Starting ScreenCaptureService...", Toast.LENGTH_SHORT).show()
                val captureIntent = Intent(this, ScreenCaptureService::class.java)
                captureIntent.putExtra("start", true)
                startForegroundService(captureIntent)
            } else {
                Toast.makeText(this, "ERROR: resultCode=$resultCode data=$data", Toast.LENGTH_LONG).show()
            }
        }, 500) // 500ms delay

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "MLBB Overlay",
                NotificationManager.IMPORTANCE_LOW
            ).apply { description = "Shows MLBB draft recommendations" }
            (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Draft Assistant")
            .setContentText("Overlay active")
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
                @Suppress("DEPRECATION")
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = 8
            y = 120
        }

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

        windowManager.addView(overlayView, params)
        Log.d(TAG, "Overlay view added")
    }

    override fun onDestroy() {
        super.onDestroy()
        DraftUpdateManager.removeListener(updateCallback)
        if (::windowManager.isInitialized && ::overlayView.isInitialized) {
            windowManager.removeView(overlayView)
        }
        Log.d(TAG, "OverlayService destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
