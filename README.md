# CyberWand 赛博魔杖

> 挥一挥，蓝牙送出 — 极简的手势识别蓝牙设备

**版本**: v3.0（极简版）  
**状态**: 工程样机阶段  
**最后更新**: 2026-04-17

---

## 🎯 产品定位

CyberWand 是一款 **手势识别 + 蓝牙发送/广播** 的可穿戴 / 手持交互设备。核心价值：

1. **握在手里就能用** — MPU6050 六轴 IMU 捕捉运动，ESP32-S3 本地 CNN 识别手势
2. **开口即广播** — 识别结果通过 BLE 以两种方式送出：
    - 对已连接客户端（手机/PC/下游设备）通过 GATT NOTIFY 发送
    - 无连接时直接更新 BLE 广播包的 Manufacturer Data，周围扫描者直接获取
3. **硬件极简** — 无屏幕、无 SD 卡、无音频，只有 MCU + IMU + 电源 + 单按键 + 状态 LED

---

## 📁 项目结构

```
CyberWand_Insta360/
├── HardWare/                       # 硬件设计
│   ├── HardWare/                   # 硬件文档（规格书 / 物料 / 连接指南）
│   └── schematic/skidl/            # SKiDL 电路描述（Python）
│       ├── cyberwand_circuit.py    # 主电路（v3.0 极简版）
│       ├── esp32_s3_wroom.py       # ESP32-S3 定义
│       ├── mpu6050_part.py         # MPU6050 定义
│       └── ...                     # 电源 / USB / 无源器件等
├── Software/                       # 固件（PlatformIO + Arduino Core）
│   ├── src/main.cpp                # 主程序（IMU 采集 → CNN 识别 → BLE 发送）
│   ├── lib/                        # 模块：imu / cnn / button / led / base / common
│   ├── include/                    # 共用头文件
│   ├── platformio.ini              # 构建配置
│   ├── model.h5 / weights.h        # 训练好的手势识别模型
│   └── TraningData_4_19/           # 最新采集到的训练数据
├── TrainningData/                  # 旧训练数据（保留作参考）
├── host_program/
│   └── cyberwand_gui/              # PyQt 上位机（BLE 连接 + 手势配置）
├── userstory/userstory.md          # 用户故事 / 需求文档
├── enclosure/                      # 3D 外壳设计（v4 葡萄藤雕花魔杖 elder_wand.scad / elder_wand_design.md）
├── doc/                            # 芯片手册（ESP32 / MPU6050 / TP4056 / USB）
└── archives/                       # 历史版本归档
```

---

## 🚀 快速开始

### 编译与烧录固件

```bash
cd Software
pio run                 # 编译
pio run -t upload       # 烧录
pio device monitor      # 串口监视
```

### 上位机（可选）

```bash
cd host_program/cyberwand_gui
pip install -r requirements.txt
python src/main.py
```

### 生成电路网表

```bash
cd HardWare/schematic/skidl
python cyberwand_circuit.py    # 执行 ERC 并生成 KiCad 网表
```

---

## 📊 技术规格

| 项目 | 规格 |
|------|------|
| **主控** | ESP32-S3-WROOM-1N16R8（16MB Flash + 8MB PSRAM） |
| **无线** | BLE 5.0（GATT Notify + 广播双模发送） |
| **传感器** | MPU6050 六轴 IMU（I2C） |
| **识别框架** | nnom CNN（本地推理，无需联网） |
| **电源** | USB Type-C + TP4056 充电 + ME6211 LDO |
| **电池** | 603040 锂电池 800mAh |
| **交互** | 单键多功能（单击 / 双击 / 长按） + 系统状态 LED |
| **指示** | 充电/充满 LED（由 TP4056 直接驱动） |

---

## 🎮 交互方式

- **单击** — 触发一次手势采集 + 识别 + BLE 发送/广播
- **双击** — 在 **应用模式** ⇄ **采集模式** 之间切换
- **长按** — 长段 IMU 数据采集（用于验证 / 导出）

详见 `userstory/userstory.md`。

---

## 📡 BLE 接口

| 项目 | 值 |
|---|---|
| 设备名 | `CyberWand` |
| 主服务 UUID | `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` |
| TX 特征 UUID | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`（NOTIFY + READ） |

**默认手势映射**（固件内，后续可通过上位机改写到 NVS）：

| 手势 ID | BLE 字符串 |
|---|---|
| 0 | `GESTURE_CIRCLE` |
| 1 | `GESTURE_LIGHTNING` |
| 2 | `GESTURE_H` |
| 3 | `GESTURE_W` |

---

## 🛠️ 开发状态

| 阶段 | 状态 | 说明 |
|---|---|---|
| 产品定义 | ✅ 完成 | `userstory/userstory.md` 极简版 |
| 电路设计 | ✅ 完成 | `HardWare/schematic/skidl/cyberwand_circuit.py` v3.0 |
| 固件 MVP | 🚧 进行中 | IMU/CNN/按键/LED 就绪，BLE 骨架已接入 |
| 硬件打样 | ⏳ 待执行 | |
| 整机验证 | ⏳ 待执行 | |

---

## 📦 archives 说明

`archives/` 保留各历史版本：v34~v210 外壳渲染、旧版 firmware、旧 host、旧设计文档等，需要时可回溯，当前主干不依赖。

---

## 📜 许可证

Apache-2.0
