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
        private const val OVERLAY_PERMISSION_REQUEST_CODE = 1001
        private const val SCREEN_CAPTURE_REQUEST_CODE = 1002
        private const val POST_NOTIFICATIONS_REQUEST_CODE = 1003
    }

    private lateinit var btnStartOverlay: Button
    private lateinit var btnStopOverlay: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        btnStartOverlay = findViewById(R.id.btn_start_overlay)
        btnStopOverlay = findViewById(R.id.btn_stop_overlay)

        btnStartOverlay.setOnClickListener {
            Log.d(TAG, "Button clicked - Start Overlay")
            checkAndRequestPermissions()
        }

        btnStopOverlay.setOnClickListener {
            Log.d(TAG, "Button clicked - Stop Overlay")
            stopOverlayService()
        }

        updateButtonStates()
        Log.d(TAG, "MainActivity created")
    }

    private fun checkAndRequestPermissions() {
        Log.d(TAG, "checkAndRequestPermissions called")

        val permissionsNeeded = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
                android.content.pm.PackageManager.PERMISSION_GRANTED) {
                permissionsNeeded.add(Manifest.permission.POST_NOTIFICATIONS)
                Log.d(TAG, "POST_NOTIFICATIONS permission needed")
            }
        }

        if (permissionsNeeded.isNotEmpty()) {
            Log.d(TAG, "Requesting permissions: $permissionsNeeded")
            ActivityCompat.requestPermissions(this, permissionsNeeded.toTypedArray(),
                POST_NOTIFICATIONS_REQUEST_CODE)
        } else {
            checkOverlayPermission()
        }
    }

    private fun checkOverlayPermission() {
        Log.d(TAG, "Checking overlay permission")
        if (!Settings.canDrawOverlays(this)) {
            Log.d(TAG, "Overlay permission NOT granted - opening settings")
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            startActivityForResult(intent, OVERLAY_PERMISSION_REQUEST_CODE)
        } else {
            Log.d(TAG, "Overlay permission already granted")
            requestScreenCapture()
        }
    }

    private fun requestScreenCapture() {
        Log.d(TAG, "Requesting screen capture permission")
        val mediaProjectionManager = getSystemService(MediaProjectionManager::class.java)
        startActivityForResult(
            mediaProjectionManager.createScreenCaptureIntent(),
            SCREEN_CAPTURE_REQUEST_CODE
        )
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        Log.d(TAG, "onActivityResult: requestCode=$requestCode, resultCode=$resultCode")

        when (requestCode) {
            OVERLAY_PERMISSION_REQUEST_CODE -> {
                Log.d(TAG, "Overlay permission result: ${Settings.canDrawOverlays(this)}")
                if (Settings.canDrawOverlays(this)) {
                    Log.d(TAG, "Overlay permission granted - requesting screen capture")
                    requestScreenCapture()
                } else {
                    Toast.makeText(this, "Overlay permission required", Toast.LENGTH_SHORT).show()
                    Log.w(TAG, "Overlay permission denied by user")
                }
            }
            SCREEN_CAPTURE_REQUEST_CODE -> {
                if (resultCode == Activity.RESULT_OK && data != null) {
                    Log.d(TAG, "Screen capture permission granted - starting overlay service")
                    startOverlayService(resultCode, data)
                } else {
                    Toast.makeText(this, "Screen capture permission required", Toast.LENGTH_SHORT).show()
                    Log.w(TAG, "Screen capture permission denied by user")
                }
            }
        }
    }

    private fun startOverlayService(resultCode: Int, data: Intent) {
        Log.d(TAG, "Starting OverlayService")
        val serviceIntent = Intent(this, OverlayService::class.java).apply {
            putExtra("resultCode", resultCode)
            putExtra("data", data)
        }
        ContextCompat.startForegroundService(this, serviceIntent)
        updateButtonStates()
        Toast.makeText(this, "Overlay started", Toast.LENGTH_SHORT).show()
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
