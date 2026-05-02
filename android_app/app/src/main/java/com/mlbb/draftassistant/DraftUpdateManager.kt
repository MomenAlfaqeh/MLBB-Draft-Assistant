package com.mlbb.draftassistant

import android.os.Handler
import android.os.Looper
import android.util.Log

interface DraftUpdateListener {
    fun onDraftUpdate(winProbability: Double, recommendations: String)
}

object DraftUpdateManager {
    private const val TAG = "DraftUpdateManager"
    private val listeners = mutableListOf<DraftUpdateListener>()
    private val handler = Handler(Looper.getMainLooper())

    fun registerListener(listener: DraftUpdateListener) {
        synchronized(listeners) {
            listeners.add(listener)
            Log.d(TAG, "Listener registered, total listeners: ${listeners.size}")
        }
    }

    fun unregisterListener(listener: DraftUpdateListener) {
        synchronized(listeners) {
            listeners.remove(listener)
            Log.d(TAG, "Listener unregistered, total listeners: ${listeners.size}")
        }
    }

    fun notifyUpdate(winProbability: Double, recommendations: String) {
        synchronized(listeners) {
            Log.d(TAG, "Notifying ${listeners.size} listeners: win=$winProbability")
            // Run on main thread since listeners will update UI
            handler.post {
                listeners.forEach { listener ->
                    try {
                        listener.onDraftUpdate(winProbability, recommendations)
                    } catch (e: Exception) {
                        Log.e(TAG, "Error notifying listener: ${e.message}")
                    }
                }
            }
        }
    }
}
