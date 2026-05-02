package com.mlbb.draftassistant

import android.os.Handler
import android.os.Looper

object DraftUpdateManager {
    var winProbability: Double = 0.0
    var recommendations: String = "Analyzing draft..."
    private val listeners = mutableListOf<() -> Unit>()
    private val handler = Handler(Looper.getMainLooper())

    fun addListener(callback: () -> Unit) {
        listeners.add(callback)
    }

    fun removeListener(callback: () -> Unit) {
        listeners.remove(callback)
    }

    fun notifyUpdate(win: Double, recs: String) {
        winProbability = win
        recommendations = recs
        handler.post {
            listeners.forEach { it() }
        }
    }
}
