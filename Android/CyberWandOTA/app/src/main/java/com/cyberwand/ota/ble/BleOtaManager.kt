package com.cyberwand.ota.ble

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

@SuppressLint("MissingPermission")
class BleOtaManager(private val context: Context) {

    companion object {
        private const val TAG = "BleOta"
        val OTA_SERVICE_UUID: UUID = UUID.fromString("0000fe00-0000-1000-8000-00805f9b34fb")
        val OTA_CTRL_UUID: UUID = UUID.fromString("0000fe01-0000-1000-8000-00805f9b34fb")
        val OTA_DATA_UUID: UUID = UUID.fromString("0000fe02-0000-1000-8000-00805f9b34fb")
        val OTA_STATUS_UUID: UUID = UUID.fromString("0000fe03-0000-1000-8000-00805f9b34fb")
        val OTA_VERSION_UUID: UUID = UUID.fromString("0000fe04-0000-1000-8000-00805f9b34fb")
        val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        const val TARGET_DEVICE_NAME = "CyberWand"
        private const val SCAN_TIMEOUT_MS = 15000L
        private const val CHUNK_DELAY_MS = 10L
    }

    sealed class State {
        object Idle : State()
        object Scanning : State()
        data class Connected(val deviceName: String) : State()
        data class Uploading(val progress: Int) : State()
        object Success : State()
        data class Error(val message: String) : State()
    }

    private val _state = MutableStateFlow<State>(State.Idle)
    val state: StateFlow<State> = _state

    private val _deviceVersion = MutableStateFlow<String?>(null)
    val deviceVersion: StateFlow<String?> = _deviceVersion

    private var gatt: BluetoothGatt? = null
    private var ctrlChar: BluetoothGattCharacteristic? = null
    private var dataChar: BluetoothGattCharacteristic? = null
    private var statusChar: BluetoothGattCharacteristic? = null
    private var versionChar: BluetoothGattCharacteristic? = null
    private var firmwareData: ByteArray? = null
    private var mtu = 23
    private val handler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val scanner by lazy {
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager)
            .adapter.bluetoothLeScanner
    }

    fun scanAndConnect() {
        Log.i(TAG, "scanAndConnect: starting scan for '$TARGET_DEVICE_NAME'")
        _state.value = State.Scanning
        _deviceVersion.value = null
        val filter = ScanFilter.Builder().setDeviceName(TARGET_DEVICE_NAME).build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        scanner.startScan(listOf(filter), settings, scanCallback)
        handler.postDelayed({
            scanner.stopScan(scanCallback)
            if (_state.value is State.Scanning) {
                Log.w(TAG, "scanAndConnect: timeout, device not found")
                _state.value = State.Error("未找到设备 $TARGET_DEVICE_NAME")
            }
        }, SCAN_TIMEOUT_MS)
    }

    fun disconnect() {
        Log.i(TAG, "disconnect: closing GATT")
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        _state.value = State.Idle
        _deviceVersion.value = null
    }

    fun startOta(firmware: ByteArray) {
        Log.i(TAG, "startOta: firmware size=${firmware.size}")
        firmwareData = firmware
        val ctrl = ctrlChar ?: run {
            Log.e(TAG, "startOta: ctrlChar is null, OTA service not discovered")
            _state.value = State.Error("OTA Service 未找到")
            return
        }
        val size = firmware.size
        val cmd = byteArrayOf(
            0x01,
            (size and 0xFF).toByte(),
            (size shr 8 and 0xFF).toByte(),
            (size shr 16 and 0xFF).toByte(),
            (size shr 24 and 0xFF).toByte()
        )
        ctrl.value = cmd
        ctrl.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        val ok = gatt?.writeCharacteristic(ctrl) ?: false
        if (!ok) {
            Log.e(TAG, "startOta: writeCharacteristic START failed")
            _state.value = State.Error("发送 START 命令失败")
            return
        }
        _state.value = State.Uploading(0)
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            Log.i(TAG, "onScanResult: found ${result.device.name} [${result.device.address}]")
            scanner.stopScan(this)
            handler.removeCallbacksAndMessages(null)
            result.device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
        }

        override fun onScanFailed(errorCode: Int) {
            Log.e(TAG, "onScanFailed: errorCode=$errorCode")
            _state.value = State.Error("BLE 扫描失败 (code=$errorCode)")
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            Log.i(TAG, "onConnectionStateChange: status=$status newState=$newState")
            if (newState == BluetoothProfile.STATE_CONNECTED && status == BluetoothGatt.GATT_SUCCESS) {
                gatt = g
                g.requestMtu(517)
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.w(TAG, "disconnected: status=$status")
                val wasUploading = _state.value is State.Uploading
                _state.value = if (wasUploading) State.Error("传输中断连") else State.Idle
                _deviceVersion.value = null
                g.close()
            } else if (status != BluetoothGatt.GATT_SUCCESS) {
                Log.e(TAG, "connection failed: status=$status")
                _state.value = State.Error("连接失败 (status=$status)")
                g.close()
            }
        }

        override fun onMtuChanged(g: BluetoothGatt, newMtu: Int, status: Int) {
            mtu = newMtu
            Log.i(TAG, "onMtuChanged: mtu=$newMtu status=$status")
            g.discoverServices()
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            Log.i(TAG, "onServicesDiscovered: status=$status")
            if (status != BluetoothGatt.GATT_SUCCESS) {
                _state.value = State.Error("服务发现失败")
                return
            }
            val otaSvc = g.getService(OTA_SERVICE_UUID)
            if (otaSvc == null) {
                Log.e(TAG, "OTA service (0xFE00) not found on device")
                _state.value = State.Error("设备不支持 OTA 升级")
                return
            }
            ctrlChar = otaSvc.getCharacteristic(OTA_CTRL_UUID)
            dataChar = otaSvc.getCharacteristic(OTA_DATA_UUID)
            statusChar = otaSvc.getCharacteristic(OTA_STATUS_UUID)
            versionChar = otaSvc.getCharacteristic(OTA_VERSION_UUID)

            Log.d(TAG, "chars: ctrl=${ctrlChar!=null} data=${dataChar!=null} " +
                "status=${statusChar!=null} version=${versionChar!=null}")

            // Subscribe to status notifications
            statusChar?.let { ch ->
                g.setCharacteristicNotification(ch, true)
                ch.getDescriptor(CCCD_UUID)?.let { desc ->
                    desc.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                    g.writeDescriptor(desc)
                }
            }

            _state.value = State.Connected(g.device.name ?: "Unknown")
        }

        override fun onDescriptorWrite(g: BluetoothGatt, desc: BluetoothGattDescriptor, status: Int) {
            Log.d(TAG, "onDescriptorWrite: status=$status")
            // After CCCD write completes, read device version
            versionChar?.let { g.readCharacteristic(it) }
        }

        override fun onCharacteristicRead(g: BluetoothGatt, ch: BluetoothGattCharacteristic, status: Int) {
            if (ch.uuid == OTA_VERSION_UUID) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    val v = ch.value
                    if (v != null && v.size >= 3) {
                        val ver = "${v[0].toInt() and 0xFF}.${v[1].toInt() and 0xFF}.${v[2].toInt() and 0xFF}"
                        Log.i(TAG, "device firmware version: $ver")
                        _deviceVersion.value = ver
                    } else {
                        Log.w(TAG, "version read: unexpected data size=${v?.size}")
                    }
                } else {
                    Log.w(TAG, "version read failed: status=$status")
                }
            }
        }

        override fun onCharacteristicWrite(g: BluetoothGatt, ch: BluetoothGattCharacteristic, status: Int) {
            if (ch.uuid == OTA_CTRL_UUID) {
                Log.d(TAG, "onCharacteristicWrite CTRL: status=$status")
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    Log.e(TAG, "CTRL write failed, aborting OTA")
                    _state.value = State.Error("控制命令写入失败")
                    firmwareData = null
                    return
                }
                if (firmwareData != null &&
                    _state.value is State.Uploading &&
                    (_state.value as State.Uploading).progress == 0) {
                    Log.i(TAG, "START acknowledged, beginning data transfer")
                    scope.launch { sendFirmwareData() }
                }
            }
        }

        override fun onCharacteristicChanged(g: BluetoothGatt, ch: BluetoothGattCharacteristic) {
            if (ch.uuid == OTA_STATUS_UUID) {
                val data = ch.value ?: return
                if (data.isEmpty()) return
                val code = data[0].toInt() and 0xFF
                val extra = if (data.size >= 5) {
                    (data[1].toInt() and 0xFF) or
                    ((data[2].toInt() and 0xFF) shl 8) or
                    ((data[3].toInt() and 0xFF) shl 16) or
                    ((data[4].toInt() and 0xFF) shl 24)
                } else 0

                Log.d(TAG, "OTA status: code=0x${code.toString(16)} extra=$extra")

                when (code) {
                    0x01 -> Log.i(TAG, "device READY")
                    0x02 -> _state.value = State.Uploading(extra)
                    0x03 -> {
                        Log.i(TAG, "OTA SUCCESS, device rebooting")
                        _state.value = State.Success
                        firmwareData = null
                    }
                    in 0xE0..0xFF -> {
                        val msg = when(code) {
                            0xE0 -> "OTA 初始化失败"
                            0xE1 -> "写入失败"
                            0xE2 -> "固件验证失败"
                            0xE3 -> "固件大小错误"
                            0xE4 -> "已取消"
                            else -> "错误 0x${code.toString(16)}"
                        }
                        Log.e(TAG, "OTA ERROR: $msg (code=0x${code.toString(16)})")
                        _state.value = State.Error(msg)
                        firmwareData = null
                    }
                }
            }
        }
    }

    private suspend fun sendFirmwareData() {
        val fw = firmwareData ?: return
        val g = gatt ?: run {
            Log.e(TAG, "sendFirmwareData: gatt is null")
            _state.value = State.Error("BLE 连接丢失")
            return
        }
        val ch = dataChar ?: run {
            Log.e(TAG, "sendFirmwareData: dataChar is null")
            _state.value = State.Error("OTA Data 特征未找到")
            return
        }
        val chunkSize = (mtu - 3).coerceAtMost(500)
        Log.i(TAG, "sendFirmwareData: size=${fw.size} mtu=$mtu chunkSize=$chunkSize")

        var offset = 0
        while (offset < fw.size) {
            if (gatt == null) {
                Log.e(TAG, "sendFirmwareData: connection lost at offset=$offset")
                _state.value = State.Error("传输中连接断开")
                return
            }
            val end = (offset + chunkSize).coerceAtMost(fw.size)
            ch.value = fw.copyOfRange(offset, end)
            ch.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
            g.writeCharacteristic(ch)
            offset = end
            delay(CHUNK_DELAY_MS)
        }

        Log.i(TAG, "sendFirmwareData: all data sent, sending END")
        delay(500)
        ctrlChar?.let { ctrl ->
            ctrl.value = byteArrayOf(0x02)
            ctrl.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            g.writeCharacteristic(ctrl)
        }
    }

    fun destroy() {
        Log.i(TAG, "destroy")
        scope.cancel()
        disconnect()
    }
}
