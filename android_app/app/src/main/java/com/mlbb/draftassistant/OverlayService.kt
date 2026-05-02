package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
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
import androidx.core.app.NotificationCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import org.json.JSONObject
import org.json.JSONArray

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

    private val draftUpdateReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            val winProb = intent?.getDoubleExtra("win_probability", 0.0) ?: 0.0
            val recommendationsJson = intent?.getStringExtra("recommendations") ?: "{}"

            val winRateText = overlayView.findViewById<TextView>(R.id.tv_win_probability)
            val laneText = overlayView.findViewById<TextView>(R.id.tv_lane_recommendations)

            // Update win probability
            winRateText.text = "Win: ${(winProb * 100).toInt()}%"

            // Parse recommendations JSON
            try {
                val json = JSONObject(recommendationsJson)
                val sb = StringBuilder()
                val laneOrder = listOf("EXP", "Jungle", "Mid", "Gold", "Roam")
                for (lane in laneOrder) {
                    val heroes = json.optJSONArray(lane) ?: json.optJSONArray(lane.lowercase()) ?: continue
                    if (heroes.length() == 0) continue
                    val top = (0 until minOf(2, heroes.length())).map { heroes.getJSONObject(it) }
                    val names = top.joinToString(" / ") { it.getString("name") }
                    val pct = top.firstOrNull()?.let {
                        "${(it.optDouble("total_score", 0.0) * 100).toInt()}%"
                    } ?: ""
                    sb.appendLine("[$lane] $names  $pct")
                }
                laneText.text = sb.toString().trimEnd()
            } catch (e: Exception) {
                Log.e(TAG, "Error parsing recommendations: ${e.message}")
                laneText.text = "Analyzing draft..."
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "OverlayService created")
        createNotificationChannel()
        setupOverlay()
        registerBroadcastReceiver()
    }

    private fun registerBroadcastReceiver() {
        val filter = IntentFilter("DRAFT_UPDATE")
        LocalBroadcastManager.getInstance(this).registerReceiver(draftUpdateReceiver, filter)
        Log.d(TAG, "Registered DRAFT_UPDATE receiver")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "OverlayService started")
        startForeground(NOTIFICATION_ID, createNotification())
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "MLBB Overlay Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply { description = "Shows MLBB draft recommendations" }
            (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MLBB Draft Assistant")
            .setContentText("Overlay active · Analyzing draft...")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

    private fun setupOverlay() {
        Log.d(TAG, "Setting up overlay")
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

        setupDragListener(params)
        windowManager.addView(overlayView, params)
        Log.d(TAG, "Overlay view added")
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

    override fun onDestroy() {
        Log.d(TAG, "OverlayService destroyed")
        super.onDestroy()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(draftUpdateReceiver)
        if (::windowManager.isInitialized && ::overlayView.isInitialized) {
            windowManager.removeView(overlayView)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
