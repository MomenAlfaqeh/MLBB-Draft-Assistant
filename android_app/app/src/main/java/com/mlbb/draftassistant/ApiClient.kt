package com.mlbb.draftassistant

import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.util.concurrent.TimeUnit

interface MLBBApiService {
    @GET("api/recommendations")
    suspend fun getRecommendations(): List<Recommendation>

    @Multipart
    @POST("api/analyze-screenshot")
    suspend fun analyzeScreenshot(@Part screenshot: MultipartBody.Part): DraftState
}

data class DraftState(
    val allies: List<String> = emptyList(),
    val enemies: List<String> = emptyList(),
    val currentTurn: String = "",
    val isComplete: Boolean = false
)

class ApiClient {
    private val baseUrl = "https://mlbb-draft-assistant-g19m.onrender.com/"

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    private val apiService = retrofit.create(MLBBApiService::class.java)

    suspend fun getRecommendations(): List<Recommendation> {
        return try {
            apiService.getRecommendations()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun analyzeScreenshot(imageBytes: ByteArray): DraftState {
        return try {
            val requestBody = imageBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
            val multipartBody = MultipartBody.Part.createFormData(
                "screenshot",
                "screenshot.jpg",
                requestBody
            )
            apiService.analyzeScreenshot(multipartBody)
        } catch (e: Exception) {
            DraftState()
        }
    }
}
