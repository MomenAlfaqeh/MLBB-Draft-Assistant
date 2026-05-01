package com.mlbb.draftassistant

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.Looper
import android.util.Log

/**
 * Handles MediaProjection screen capture.
 * Used as a plain class (not a Service) - initialized and controlled by OverlayService.
 */
class ScreenCaptureService {

    companion object {
        private const val TAG = "MLBBScreenCapture"
        private const val VIRTUAL_DISPLAY_NAME = "MLBB_ScreenCapture"
    }

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null

    private val handler = Handler(Looper.getMainLooper())
    private var screenWidth = 0
    private var screenHeight = 0
    private var screenDensity = 0

    // Latest captured bitmap (thread-safe read from OverlayService)
    @Volatile private var latestBitmap: Bitmap? = null

    fun startCapture(context: Context, resultCode: Int, data: Intent) {
        Log.d(TAG, "Starting screen capture")
        val manager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        mediaProjection = manager.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(mediaProjectionCallback, handler)

        val metrics = context.resources.displayMetrics
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
            handler
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
                }
            } catch (e: Exception) {
                Log.e(TAG, "Image listener error: ${e.message}")
            } finally {
                image.close()
            }
        }, handler)
    }

    /** Returns the most recently captured screen bitmap, or null if none yet */
    fun getLatestBitmap(): Bitmap? = latestBitmap?.copy(latestBitmap!!.config!!, false)

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

    fun stopCapture() {
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
}
