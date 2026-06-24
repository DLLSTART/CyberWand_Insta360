package com.cyberwand.ota

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class FirmwareInfo(
    val version: String,
    val size: Long,
    val sha256: String,
    val downloadUrl: String
)

class FirmwareRepository {
    companion object {
        private const val TAG = "FwRepo"
        const val BASE_URL = "http://39.96.83.115:6666"
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    suspend fun getLatestVersion(product: String = "cyberwand"): FirmwareInfo? =
        withContext(Dispatchers.IO) {
            try {
                val url = "$BASE_URL/firmware/latest?product=$product"
                Log.i(TAG, "getLatestVersion: GET $url")
                val req = Request.Builder().url(url).build()
                val resp = client.newCall(req).execute()
                if (!resp.isSuccessful) {
                    Log.w(TAG, "getLatestVersion: HTTP ${resp.code}")
                    return@withContext null
                }
                val body = resp.body?.string() ?: return@withContext null
                val json = JSONObject(body)
                if (!json.optBoolean("ok", false)) {
                    Log.w(TAG, "getLatestVersion: server returned ok=false")
                    return@withContext null
                }
                val info = FirmwareInfo(
                    version = json.getString("version"),
                    size = json.getLong("size"),
                    sha256 = json.getString("sha256"),
                    downloadUrl = "$BASE_URL${json.getString("url")}"
                )
                Log.i(TAG, "getLatestVersion: v${info.version} size=${info.size}")
                info
            } catch (e: Exception) {
                Log.e(TAG, "getLatestVersion failed: ${e.message}", e)
                null
            }
        }

    suspend fun downloadFirmware(info: FirmwareInfo): ByteArray? =
        withContext(Dispatchers.IO) {
            try {
                Log.i(TAG, "downloadFirmware: GET ${info.downloadUrl}")
                val req = Request.Builder().url(info.downloadUrl).build()
                val resp = client.newCall(req).execute()
                if (!resp.isSuccessful) {
                    Log.e(TAG, "downloadFirmware: HTTP ${resp.code}")
                    return@withContext null
                }
                val data = resp.body?.bytes()
                Log.i(TAG, "downloadFirmware: downloaded ${data?.size} bytes")
                data
            } catch (e: Exception) {
                Log.e(TAG, "downloadFirmware failed: ${e.message}", e)
                null
            }
        }
}
