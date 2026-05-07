package com.mlbb.draftassistant

import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    companion object {
        private const val TAG = "MLBB"
        private const val OVERLAY_PERMISSION_REQUEST = 1001
        private const val SCREEN_CAPTURE_REQUEST = 1002
        var projectionResultCode: Int = -1
        var projectionData: Intent? = null
    }

    private lateinit var btnStartOverlay: Button
    private lateinit var btnStopOverlay: Button
    private lateinit var mediaProjectionManager: MediaProjectionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        mediaProjectionManager = getSystemService(MediaProjectionManager::class.java)
        btnStartOverlay = findViewById(R.id.btn_start_overlay)
        btnStopOverlay = findViewById(R.id.btn_stop_overlay)

        btnStartOverlay.setOnClickListener {
            Log.d(TAG, "Button clicked - Start Overlay")
            when {
                !Settings.canDrawOverlays(this) -> {
                    Toast.makeText(this, "Checking overlay permission...", Toast.LENGTH_SHORT).show()
                    startActivityForResult(
                        Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")),
                        OVERLAY_PERMISSION_REQUEST
                    )
                }
                else -> {
                    startActivityForResult(
                        mediaProjectionManager.createScreenCaptureIntent(),
                        SCREEN_CAPTURE_REQUEST
                    )
                }
            }
        }

        btnStopOverlay.setOnClickListener {
            Log.d(TAG, "Button clicked - Stop Overlay")
            stopServices()
        }
        updateButtonStates()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        when (requestCode) {
            OVERLAY_PERMISSION_REQUEST -> {
                if (Settings.canDrawOverlays(this)) {
                    startActivityForResult(
                        mediaProjectionManager.createScreenCaptureIntent(),
                        SCREEN_CAPTURE_REQUEST
                    )
                } else {
                    Toast.makeText(this, "Overlay permission DENIED", Toast.LENGTH_SHORT).show()
                }
            }
            SCREEN_CAPTURE_REQUEST -> {
                if (resultCode == RESULT_OK && data != null) {
                    Toast.makeText(this, "Screen capture granted! Starting services...", Toast.LENGTH_SHORT).show()
                    projectionResultCode = resultCode
                    projectionData = data
                    
                    // التعديل الهام: تشغيل الخدمتين معاً (النافذة الشفافة والتصوير)
                    startForegroundService(Intent(this, OverlayService::class.java).apply { putExtra("start", true) })
                    startForegroundService(Intent(this, ScreenCaptureService::class.java))
                    
                    updateButtonStates()
                } else {
                    Toast.makeText(this, "Screen capture DENIED", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun stopServices() {
        Log.d(TAG, "Stopping Services")
        stopService(Intent(this, OverlayService::class.java))
        stopService(Intent(this, ScreenCaptureService::class.java)) // التعديل: إيقاف خدمة التصوير
        updateButtonStates()
        Toast.makeText(this, "Overlay & Capture stopped", Toast.LENGTH_SHORT).show()
    }

    private fun updateButtonStates() {
        btnStartOverlay.isEnabled = true
        btnStopOverlay.isEnabled = true
    }
}