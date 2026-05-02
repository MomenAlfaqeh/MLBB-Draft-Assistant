package com.mlbb.draftassistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.util.Base64
import android.util.Log
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
        private const val TAG = "MLBBOverlay"
        private const val CHANNEL_ID = "MLBBOverlayChannel"
        private const val NOTIFICATION_ID = 1
        private const val UPDATE_INTERVAL_MS = 1000L
    }

    private lateinit var windowManager: WindowManager
    private lateinit var overlayView: View
    private var initialX = 0
    private var initialY = 0
    private var initialTouchX = 0f
    private var initialTouchY = 0f

    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private lateinit var apiClient: ApiClient

    // Current draft state (updated from Vision Engine)
    private var currentAllyPicks = mutableListOf<String>()
    private var currentEnemyPicks = mutableListOf<String>()

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "OverlayService created")
        createNotificationChannel()
        setupOverlay()
        apiClient = ApiClient()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "OverlayService started")
        startForeground(NOTIFICATION_ID, createNotification())

        val resultCode = intent?.getIntExtra("resultCode", -1) ?: -1
        val data = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent?.getParcelableExtra("data", Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent?.getParcelableExtra<Intent>("data")
        }

        if (resultCode != -1 && data != null) {
            Log.d(TAG, "Starting screen capture service with projection data")
            val captureIntent = Intent(this, ScreenCaptureService::class.java).apply {
                putExtra("resultCode", resultCode)
                putExtra("data", data)
            }
            startForegroundService(captureIntent)
        }

        startUpdateLoop()
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

    private fun startUpdateLoop() {
        Log.d(TAG, "Starting update loop every ${UPDATE_INTERVAL_MS}ms")
        serviceScope.launch {
            // Check backend health on start
            val alive = withContext(Dispatchers.IO) { apiClient.isBackendAlive() }
            if (!alive) {
                updateOverlayStatus("⚠ Backend offline")
            }

            while (isActive) {
                updateFromScreenAndApi()
                delay(UPDATE_INTERVAL_MS)
            }
        }
    }

    private suspend fun updateFromScreenAndApi() {
        withContext(Dispatchers.IO) {
            try {
                // Step 1: Capture & analyze screen
                val bitmap = ScreenCaptureRepository.getLatestBitmap()
                if (bitmap != null) {
                    val base64 = bitmapToBase64(bitmap)
                    val draftState = apiClient.analyzeScreenshot(base64)
                    if (draftState.allies.isNotEmpty() || draftState.enemies.isNotEmpty()) {
                        currentAllyPicks = draftState.allies.toMutableList()
                        currentEnemyPicks = draftState.enemies.toMutableList()
                        Log.d(TAG, "Vision: allies=$currentAllyPicks enemies=$currentEnemyPicks")
                    }
                }

                // Step 2: Get lane recommendations based on current picks
                val response = apiClient.getDraftUpdate(
                    allyPicks = currentAllyPicks,
                    enemyPicks = currentEnemyPicks
                )

                withContext(Dispatchers.Main) {
                    updateOverlayUI(response)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Update error: ${e.message}")
            }
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 70, stream)
        return Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)
    }

    private fun updateOverlayUI(response: DraftUpdateResponse) {
        val laneText = overlayView.findViewById<TextView>(R.id.tv_lane_recommendations)
        val winRateText = overlayView.findViewById<TextView>(R.id.tv_win_probability)

        val laneRecs = response.lane_recommendations
        if (laneRecs.isNotEmpty()) {
            val sb = StringBuilder()
            val laneOrder = listOf("EXP", "Jungle", "Mid", "Gold", "Roam")
            for (lane in laneOrder) {
                val heroes = laneRecs[lane] ?: laneRecs[lane.lowercase()] ?: continue
                if (heroes.isEmpty()) continue
                val top = heroes.take(2)
                val names = top.joinToString(" / ") { it.name }
                val pct = top.firstOrNull()?.let { "${(it.total_score * 100).toInt()}%" } ?: ""
                sb.appendLine("[$lane] $names  $pct")
            }
            laneText.text = sb.toString().trimEnd()
        } else if (response.top_picks.isNotEmpty()) {
            val top = response.top_picks.take(5)
            laneText.text = top.joinToString("\n") {
                "[${it.lane}] ${it.name}  ${(it.total_score * 100).toInt()}%"
            }
        } else {
            laneText.text = "Analyzing draft..."
        }

        val winPct = (response.matchup_probability * 100).toInt()
        winRateText.text = "Win: $winPct%"
    }

    private fun updateOverlayStatus(msg: String) {
        val laneText = overlayView.findViewById<TextView>(R.id.tv_lane_recommendations)
        laneText.text = msg
    }

    override fun onDestroy() {
        Log.d(TAG, "OverlayService destroyed")
        super.onDestroy()
        serviceScope.cancel()
        ScreenCaptureRepository.clear()
        if (::windowManager.isInitialized && ::overlayView.isInitialized) {
            windowManager.removeView(overlayView)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
