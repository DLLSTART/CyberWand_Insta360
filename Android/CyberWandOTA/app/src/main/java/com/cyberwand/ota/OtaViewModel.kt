package com.cyberwand.ota

import android.app.Application
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.cyberwand.ota.ble.BleOtaManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class OtaViewModel(app: Application) : AndroidViewModel(app) {

    companion object {
        private const val TAG = "OtaVM"
    }

    val bleManager = BleOtaManager(app.applicationContext)
    private val repo = FirmwareRepository()

    private val _serverFirmware = MutableStateFlow<FirmwareInfo?>(null)
    val serverFirmware: StateFlow<FirmwareInfo?> = _serverFirmware

    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message

    private val _needsUpdate = MutableStateFlow(false)
    val needsUpdate: StateFlow<Boolean> = _needsUpdate

    fun connectDevice() {
        Log.i(TAG, "connectDevice")
        bleManager.scanAndConnect()
    }

    fun disconnect() {
        Log.i(TAG, "disconnect")
        bleManager.disconnect()
        _serverFirmware.value = null
        _needsUpdate.value = false
    }

    fun checkServerVersion() {
        viewModelScope.launch {
            Log.i(TAG, "checkServerVersion: querying...")
            _message.value = "正在查询服务器版本..."
            val info = repo.getLatestVersion()
            _serverFirmware.value = info
            if (info == null) {
                _message.value = "无法连接服务器"
                _needsUpdate.value = false
                return@launch
            }

            val deviceVer = bleManager.deviceVersion.value
            Log.i(TAG, "checkServerVersion: device=$deviceVer server=${info.version}")

            if (deviceVer == null) {
                _message.value = "无法读取设备版本, 建议升级"
                _needsUpdate.value = true
            } else {
                val cmp = compareVersions(deviceVer, info.version)
                if (cmp < 0) {
                    _message.value = "设备 v$deviceVer < 服务器 v${info.version}, 需要升级"
                    _needsUpdate.value = true
                } else {
                    _message.value = "设备已是最新版本 (v$deviceVer)"
                    _needsUpdate.value = false
                }
            }
        }
    }

    fun downloadAndUpgrade() {
        val info = _serverFirmware.value ?: return
        viewModelScope.launch {
            Log.i(TAG, "downloadAndUpgrade: v${info.version} size=${info.size}")
            _message.value = "正在下载固件 (${info.size / 1024} KB)..."
            val data = repo.downloadFirmware(info)
            if (data == null) {
                Log.e(TAG, "downloadAndUpgrade: download failed")
                _message.value = "下载失败"
                return@launch
            }
            _message.value = "下载完成, 开始 BLE 传输..."
            bleManager.startOta(data)
        }
    }

    private fun compareVersions(a: String, b: String): Int {
        val pa = a.split(".").map { it.toIntOrNull() ?: 0 }
        val pb = b.split(".").map { it.toIntOrNull() ?: 0 }
        for (i in 0 until maxOf(pa.size, pb.size)) {
            val va = pa.getOrElse(i) { 0 }
            val vb = pb.getOrElse(i) { 0 }
            if (va != vb) return va.compareTo(vb)
        }
        return 0
    }

    override fun onCleared() {
        Log.i(TAG, "onCleared")
        bleManager.destroy()
        super.onCleared()
    }
}
