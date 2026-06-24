package com.cyberwand.ota

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import com.cyberwand.ota.ble.BleOtaManager

class MainActivity : ComponentActivity() {

    private lateinit var viewModel: OtaViewModel

    private val permLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        if (results.values.all { it }) viewModel.connectDevice()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        viewModel = ViewModelProvider(this)[OtaViewModel::class.java]
        setContent { MaterialTheme { OtaScreen(viewModel) { requestPermsAndConnect() } } }
    }

    private fun requestPermsAndConnect() {
        val perms = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION)
        if (Build.VERSION.SDK_INT >= 31) {
            perms.add(Manifest.permission.BLUETOOTH_SCAN)
            perms.add(Manifest.permission.BLUETOOTH_CONNECT)
        }
        val needed = perms.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (needed.isEmpty()) viewModel.connectDevice()
        else permLauncher.launch(needed.toTypedArray())
    }
}

@Composable
fun OtaScreen(vm: OtaViewModel, onConnect: () -> Unit) {
    val bleState by vm.bleManager.state.collectAsState()
    val deviceVer by vm.bleManager.deviceVersion.collectAsState()
    val serverFw by vm.serverFirmware.collectAsState()
    val message by vm.message.collectAsState()
    val needsUpdate by vm.needsUpdate.collectAsState()

    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("CyberWand OTA 升级", fontSize = 24.sp,
                color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(32.dp))

            // Device status
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("设备状态", fontSize = 14.sp, color = Color.Gray)
                    Spacer(Modifier.height(8.dp))
                    val (statusText, statusColor) = when (val s = bleState) {
                        is BleOtaManager.State.Idle -> "未连接" to Color.Gray
                        is BleOtaManager.State.Scanning -> "正在搜索..." to Color.Gray
                        is BleOtaManager.State.Connected -> "已连接: ${s.deviceName}" to Color(0xFF4CAF50)
                        is BleOtaManager.State.Uploading -> "正在升级: ${s.progress}%" to Color(0xFF2196F3)
                        is BleOtaManager.State.Success -> "升级成功! 设备已重启" to Color(0xFF4CAF50)
                        is BleOtaManager.State.Error -> "错误: ${s.message}" to Color.Red
                    }
                    Text(statusText, fontSize = 18.sp, color = statusColor)
                    if (deviceVer != null) {
                        Spacer(Modifier.height(4.dp))
                        Text("设备固件: v$deviceVer", fontSize = 14.sp, color = Color.Gray)
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // Version comparison
            if (serverFw != null) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("服务器最新版本", fontSize = 14.sp, color = Color.Gray)
                        Spacer(Modifier.height(8.dp))
                        Text("v${serverFw!!.version}  (${serverFw!!.size / 1024} KB)",
                            fontSize = 16.sp)
                        if (needsUpdate) {
                            Text("⬆ 有新版本可用", fontSize = 14.sp, color = Color(0xFFFF9800))
                        } else if (deviceVer != null) {
                            Text("✓ 已是最新", fontSize = 14.sp, color = Color(0xFF4CAF50))
                        }
                    }
                }
            }

            Spacer(Modifier.height(12.dp))

            // Message
            message?.let { Text(it, fontSize = 14.sp, color = Color.Gray) }

            // Progress bar
            if (bleState is BleOtaManager.State.Uploading) {
                Spacer(Modifier.height(12.dp))
                LinearProgressIndicator(
                    progress = (bleState as BleOtaManager.State.Uploading).progress / 100f,
                    modifier = Modifier.fillMaxWidth().height(8.dp)
                )
            }

            Spacer(Modifier.weight(1f))

            // Buttons
            when (bleState) {
                is BleOtaManager.State.Idle, is BleOtaManager.State.Error -> {
                    Button(onClick = onConnect, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                        Text("连接魔杖")
                    }
                }
                is BleOtaManager.State.Connected -> {
                    Button(onClick = { vm.checkServerVersion() },
                        modifier = Modifier.fillMaxWidth().height(48.dp)) {
                        Text("检查更新")
                    }
                    if (needsUpdate) {
                        Spacer(Modifier.height(12.dp))
                        Button(onClick = { vm.downloadAndUpgrade() },
                            modifier = Modifier.fillMaxWidth().height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4CAF50))
                        ) { Text("下载并升级") }
                    }
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(onClick = { vm.disconnect() },
                        modifier = Modifier.fillMaxWidth().height(48.dp)) {
                        Text("断开连接")
                    }
                }
                is BleOtaManager.State.Success -> {
                    Button(onClick = onConnect, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                        Text("重新连接")
                    }
                }
                else -> {}
            }
        }
    }
}
