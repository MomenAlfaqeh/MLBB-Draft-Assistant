package com.mlbb.draftassistant

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MLBB"
        private const val OVERLAY_PERMISSION_REQUEST = 1001
        private const val SCREEN_CAPTURE_REQUEST = 1002
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
                    Log.d(TAG, "Requesting overlay permission")
                    startActivityForResult(
                        Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")),
                        OVERLAY_PERMISSION_REQUEST
                    )
                }
                else -> {
                    Log.d(TAG, "Requesting screen capture permission")
                    startActivityForResult(
                        mediaProjectionManager.createScreenCaptureIntent(),
                        SCREEN_CAPTURE_REQUEST
                    )
                }
            }
        }

        btnStopOverlay.setOnClickListener {
            Log.d(TAG, "Button clicked - Stop Overlay")
            stopOverlayService()
        }

        updateButtonStates()
        Log.d(TAG, "MainActivity created")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        Log.d(TAG, "onActivityResult: requestCode=$requestCode, resultCode=$resultCode")

        when (requestCode) {
            OVERLAY_PERMISSION_REQUEST -> {
                if (Settings.canDrawOverlays(this)) {
                    Log.d(TAG, "Overlay permission granted - requesting screen capture")
                    startActivityForResult(
                        mediaProjectionManager.createScreenCaptureIntent(),
                        SCREEN_CAPTURE_REQUEST
                    )
                } else {
                    Toast.makeText(this, "Overlay permission required", Toast.LENGTH_SHORT).show()
                    Log.w(TAG, "Overlay permission denied by user")
                }
            }
            SCREEN_CAPTURE_REQUEST -> {
                if (resultCode == RESULT_OK && data != null) {
                    Log.d(TAG, "Screen capture permission granted - starting overlay service")
                    val intent = Intent(this, OverlayService::class.java).apply {
                        putExtra("resultCode", resultCode)
                        putExtra("data", data)
                    }
                    startForegroundService(intent)
                    updateButtonStates()
                    Toast.makeText(this, "Overlay started", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, "Screen capture permission required", Toast.LENGTH_SHORT).show()
                    Log.w(TAG, "Screen capture permission denied by user")
                }
            }
        }
    }

    private fun stopOverlayService() {
        Log.d(TAG, "Stopping OverlayService")
        val serviceIntent = Intent(this, OverlayService::class.java)
        stopService(serviceIntent)
        updateButtonStates()
        Toast.makeText(this, "Overlay stopped", Toast.LENGTH_SHORT).show()
    }

    private fun updateButtonStates() {
        btnStartOverlay.isEnabled = true
        btnStopOverlay.isEnabled = true
        Log.d(TAG, "Button states updated")
    }
}
