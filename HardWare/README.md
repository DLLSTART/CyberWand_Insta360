# HardWare 硬件设计目录

## 📁 目录结构

```
HardWare/
├── README.md                       # 本文件
├── cyberwand_hardware_v3.md        # 硬件设计主文档（最新 v3.0）
└── schematic/skidl/                # SKiDL 电路描述（Python）
    ├── cyberwand_circuit.py        # 主电路顶层（v3.0 极简版）
    ├── cyberwand_circuit_sklib.py  # KiCad 符号库映射
    ├── esp32_s3_wroom.py           # ESP32-S3 定义
    ├── mpu6050_part.py             # MPU6050 定义
    ├── tp4056_part.py              # TP4056 充电 IC
    ├── me6211_part.py              # ME6211 LDO
    ├── usb_type_c_part.py          # USB Type-C 连接器
    ├── usblc6_2sc6_part.py         # USB ESD 保护
    ├── ptc_fuse_part.py            # PTC 自恢复保险丝
    ├── power_switch_part.py        # 电源开关
    ├── battery_603040.py           # 锂电池
    ├── led_part.py                 # 状态 LED
    ├── passive_parts.py            # 通用电阻/电容/开关
    ├── circuit_verify.py           # 电路 ERC 验证脚本
    ├── full_verify.py              # 完整验证
    ├── simulate_voltage.py         # 电压仿真
    ├── spice_simulate.py           # SPICE 仿真
    ├── verify_circuit.py           # 符号映射验证
    ├── HARDWARE_CONNECTION_GUIDE.md# 硬件连接详解
    ├── 电路电压仿真报告.md         # 仿真报告
    └── 电路验证报告.md             # 验证报告
```

## 📖 核心文档

- **`cyberwand_hardware_v3.md`** — 硬件设计主文档（系统架构 / 选型 / 引脚分配 / PCB 规格 / BOM）
- **`schematic/skidl/cyberwand_circuit.py`** — 可执行的电路代码（唯一真相来源）
- **`schematic/skidl/HARDWARE_CONNECTION_GUIDE.md`** — 详细接线说明

## 🧩 硬件精简记录（v3.0）

相比 v2.x，v3.0 **移除** 了以下硬件：

| 被移除的硬件 | 原因 |
|---|---|
| HS20S010B TFT LCD | 去掉屏幕显示，极简交互 |
| MicroSD 卡座 | 本地存储改由 ESP32 内部 Flash / NVS 承担 |
| DFPlayer Mini + 扬声器 | 取消音频输出 |
| INMP441 I2S 麦克风 | 取消语音检测 |
| WS2812B RGB LED + SN74AHCT125 | 改为 GPIO 直驱普通状态 LED |
| 多按键（模式/选择/播放）| 合并为单键多功能（单击/双击/长按） |

**保留** 的硬件：ESP32-S3-WROOM-1 / MPU6050 / TP4056 / ME6211 / USB Type-C / USBLC6-2SC6 / PTC / 电源开关 / 603040 锂电池 / 状态 LED / 充电指示 LED × 2 / 用户按键。

## 🚀 使用方式

### 生成网表

```bash
cd schematic/skidl
python cyberwand_circuit.py
# 网表输出到 schematic/skidl/output/cyberwand_netlist.net
```

### 导入 KiCad PCB

1. 打开 KiCad，创建或打开 PCB 项目
2. 文件 → 导入 → 网表
3. 选择 `schematic/skidl/output/cyberwand_netlist.net`

## 🛠️ 维护指南

- **电路变更**：修改 `schematic/skidl/*.py`，重跑 `cyberwand_circuit.py` 生成新网表
- **新器件**：在 `schematic/skidl/` 下创建 `*_part.py`，在 `cyberwand_circuit.py` 中引用
- **文档同步**：改动后同步更新 `cyberwand_hardware_v3.md` 和 `HARDWARE_CONNECTION_GUIDE.md`

---

**最后更新**: 2026-04-17  
**当前硬件版本**: v3.0（极简版，只保留手势识别 + 蓝牙核心）
