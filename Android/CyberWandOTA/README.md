# CyberWand OTA 升级 APP

Android BLE OTA 升级应用，连接 CyberWand 魔杖，从服务器拉取最新固件并通过 BLE 传输升级。

## 功能

1. BLE 扫描并连接 "CyberWand" 设备
2. 查询服务器最新固件版本
3. 对比设备版本与服务器版本
4. 下载固件并通过 BLE OTA 传输升级
5. 升级进度实时显示

## 编译

用 Android Studio 打开本目录，等待 Gradle sync 完成后 Run 即可。

最低 API: 26 (Android 8.0)

## OTA 协议

| UUID | 用途 |
|------|------|
| 0xFE00 | OTA Service |
| 0xFE01 | Control (Write): START/END/ABORT |
| 0xFE02 | Data (Write NR): 固件分片 |
| 0xFE03 | Status (Notify): 进度/状态 |

## 服务器 API

- `GET /firmware/latest?product=cyberwand` — 查询最新版本
- `GET /firmware/download?product=cyberwand` — 下载固件
- `POST /firmware/upload` — 上传新固件 (form: product, version, file)

服务器地址: `http://39.96.83.115:6666`
