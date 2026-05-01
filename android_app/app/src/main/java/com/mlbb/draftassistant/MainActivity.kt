package com.mlbb.draftassistant

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    companion object {
        private const val REQUEST_CODE_SCREEN_CAPTURE = 1001
        private const val REQUEST_CODE_OVERLAY_PERMISSION = 1002
        private const val REQUEST_CODE_POST_NOTIFICATIONS = 1003
    }

    private lateinit var btnStartOverlay: Button
    private lateinit var btnStopOverlay: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        btnStartOverlay = findViewById(R.id.btn_start_overlay)
        btnStopOverlay = findViewById(R.id.btn_stop_overlay)

        btnStartOverlay.setOnClickListener {
            checkAndRequestPermissions()
        }

        btnStopOverlay.setOnClickListener {
            stopOverlayService()
        }

        updateButtonStates()
    }

    private fun checkAndRequestPermissions() {
        val permissionsNeeded = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
                android.content.pm.PackageManager.PERMISSION_GRANTED) {
                permissionsNeeded.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        if (permissionsNeeded.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, permissionsNeeded.toTypedArray(),
                REQUEST_CODE_POST_NOTIFICATIONS)
        } else {
            checkOverlayPermission()
        }
    }

    private fun checkOverlayPermission() {
        if (!Settings.canDrawOverlays(this)) {
            val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName"))
            startActivityForResult(intent, REQUEST_CODE_OVERLAY_PERMISSION)
        } else {
            requestScreenCapture()
        }
    }

    private fun requestScreenCapture() {
        val mediaProjectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val intent = mediaProjectionManager.createScreenCaptureIntent()
        startActivityForResult(intent, REQUEST_CODE_SCREEN_CAPTURE)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        when (requestCode) {
            REQUEST_CODE_OVERLAY_PERMISSION -> {
                if (Settings.canDrawOverlays(this)) {
                    requestScreenCapture()
                } else {
                    Toast.makeText(this, "Overlay permission required", Toast.LENGTH_SHORT).show()
                }
            }
            REQUEST_CODE_SCREEN_CAPTURE -> {
                if (resultCode == Activity.RESULT_OK && data != null) {
                    startOverlayService(resultCode, data)
                } else {
                    Toast.makeText(this, "Screen capture permission required", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun startOverlayService(resultCode: Int, data: Intent) {
        val serviceIntent = Intent(this, OverlayService::class.java).apply {
            putExtra("resultCode", resultCode)
            putExtra("data", data)
        }
        ContextCompat.startForegroundService(this, serviceIntent)
        updateButtonStates()
        Toast.makeText(this, "Overlay started", Toast.LENGTH_SHORT).show()
    }

    private fun stopOverlayService() {
        val serviceIntent = Intent(this, OverlayService::class.java)
        stopService(serviceIntent)
        updateButtonStates()
        Toast.makeText(this, "Overlay stopped", Toast.LENGTH_SHORT).show()
    }

    private fun updateButtonStates() {
        btnStartOverlay.isEnabled = true
        btnStopOverlay.isEnabled = true
    }
}
