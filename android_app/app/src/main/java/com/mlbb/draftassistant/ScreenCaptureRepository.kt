package com.mlbb.draftassistant

import android.graphics.Bitmap

object ScreenCaptureRepository {
    @Volatile
    private var _latestBitmap: Bitmap? = null

    fun updateBitmap(bitmap: Bitmap) {
        _latestBitmap?.recycle()
        _latestBitmap = bitmap
    }

    fun getLatestBitmap(): Bitmap? = _latestBitmap?.copy(_latestBitmap!!.config!!, false)

    fun clear() {
        _latestBitmap?.recycle()
        _latestBitmap = null
    }
}
