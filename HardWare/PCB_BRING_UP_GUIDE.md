# CyberWand PCB 首板调试指南 (Bring-Up Guide)

| 字段 | 值 |
|---|---|
| 适用硬件 | CyberWand v4.0 PCB (ESP32-S3-WROOM-1-N16R8 + WS2812B + InvenSense ICM 系列 IMU) |
| 适用软件 | `Software/` `feat/cyberwand-on-cyberwand-arc-bvc` 分支 (commit ≥ 引脚最终回填) |
| 原理图 | `enclosure/{充电,IMU,MCU,USB}.png` (4 张分块图) + `HardWare/schematic/` |
| PCB 几何 | `enclosure/DXF_PCB1_2026-05-01_AutoCAD2007.dxf` |
| 硬件设计文档 | `HardWare/cyberwand_hardware_v3.md` (v4.0) |
| 软件硬件配置 | `Software/include/board_config.h` |

---

## 0. 软件已为 v4.0 硬件做完的全部适配 (✅ 烧录前不需要再改任何代码)

| 项 | 改动 | 状态 |
|---|---|---|
| `platformio.ini` | `board = esp32-s3-devkitc-1`, `qio_opi` Octal PSRAM, 16MB 分区, NeoPixel 依赖 | ✅ |
| `Software/include/board_config.h` | **6 个 GPIO 常量已按原理图 MCU.png 实测填入**: `kPinKey1=2`, `kPinLed1Data=42`, `kPinI2cSda=47`, `kPinI2cScl=20`, `kPinImuInt=4`, `kPinChargeStat=5`; N16R8 PSRAM 静态断言 | ✅ |
| `lib/led/led.{h,cpp}` | 完全重写为 Adafruit NeoPixel 驱动 (RMT 时序), 保留 `LedMode` 语义 | ✅ |
| `lib/imu/mpu6050_imu.cpp` | `Wire.begin(cw::board::kPinI2cSda, cw::board::kPinI2cScl)` 显式指定 | ✅ |
| `src/main.cpp` | 全部硬编码 GPIO 替换为 `cw::board::kPinXxx`; LED 反馈升级为颜色语义 (录制=红 / 切模式=蓝快闪 / 确认=绿) | ✅ |
| 单元测试 | 56/56 PASS (CommandCodec 36 + ImuResampler 13 + RemoteFrame 4 + PairedStore 3) | ✅ |
| 固件编译 | `pio run` SUCCESS, RAM 18.8% / Flash 15.2%, `firmware.bin` 970 KB | ✅ |
| 测试代码隔离 | `verify_firmware_clean.sh` ALL CHECKS PASSED, 测试代码 0 漏入固件 | ✅ |

> 收到首板后**直接** `pio run -t upload` 即可烧录, 不需要再 `git pull` / 改 `board_config.h`. 唯一可能需要后改的情况是: 万用表回测发现某条 IO 网络与本指南不一致 → 改 `board_config.h` + `cyberwand_hardware_v3.md` §3.1.

---

## 1. 已识别的 6 项硬件设计风险 (⚠️ 上电前 / 上电时分别要核实)

详见 `cyberwand_hardware_v3.md` §0.2. 这里给出 **bring-up 阶段的具体测点 + 缓解方案**:

| # | 风险 | 测点 | 触发症状 | 缓解 |
|---|---|---|---|---|
| **R1** | I2C 没有外部 4.7K 上拉 | LDO 输出稳定后, 万用表测 SDA / SCL 静态电压 | 远低于 +3V3 (例如 2V 以下) | 在 SDA / SCL 与 +3V3 之间各飞一颗 4.7K 0402 |
| **R2** | USB-C CC1 / CC2 悬空 | 用 USB-C → USB-C 线接电脑 | 电脑不识别, VBUS 没有 5V | **改用 USB-A → USB-C 线**; 后续改板加 5.1K 双下拉 |
| **R3** | LDO1 CE 引脚接 GND | 上电瞬间断电状态下测 LDO1 pin 3 (CE) → GND 通断, 上电后测 pin 5 (VOUT) | VOUT 长期 0V → CE 高有效, LDO 关断 | 飞线把 CE 改接 VIN; 或换 CE 低有效的 LDO |
| **R4** | 充电电流 600mA 偏高 (300mAh @ 2C) | USB 充电时电池温度 (热成像 / 手摸) | 电池 > 45°C 长时间发热 | 把 R5 (PROG) 从 2 kΩ 换成 4.7 kΩ → 250mA, 或换 800mAh+ 大容量电池 |
| **R5** | IMU pin 11 标 FSYNC 但接 INT 网络 | 烧 IMU INT 中断测试程序看 IO4 是否有脉冲 | IO4 永远静默 | 软件已默认走纯轮询 (不依赖中断), 不需要任何动作 |
| **R6** | 没有 VBAT ADC 采样 | — | 软件读不到电池电量 | 后续改板加 VBAT 100K + 100K 分压 + 飞线到 IO6/IO7 等空闲 ADC1 IO |

---

## 2. 阶段 0: 烧录前的纸面检查 (15 分钟)

不上电的前提下做完, 全部通过才进入阶段 1.

### 2.1 焊接外观

- [ ] 模组 ESP32-S3-WROOM-1 与 IMU U4 没有连焊 / 飞线短路
- [ ] USB-C 接口外壳焊牢, 焊点无锡珠
- [ ] H1 (LED 级联) / H2 (电池) 排针焊接正立, 不歪斜
- [ ] LDO1 / U3 (充电 IC) / U5 (CH340) 三颗 IC 朝向 + 方向丝印一致

### 2.2 关键短路检查 (万用表蜂鸣档, 红表笔接 +3V3 / +5V / VBAT)

| 测点 1 | 测点 2 | 期望 | 实测 |
|---|---|---|---|
| +3V3 | GND | 不通 (≥ 1 kΩ) | _____ |
| +5V (USB1 pin 2) | GND | 不通 | _____ |
| VBAT (H2 pin 1) | GND | 不通 | _____ |
| LDO1 pin 1 (VIN) | LDO1 pin 5 (VOUT) | 不通 | _____ |
| MCU 模组 pin 2 (3V3) | MCU 模组 pin 1 (GND) | 不通 | _____ |
| **LDO1 pin 3 (CE)** | **GND** | **通** ⚠️ 见 R3 | _____ |

最后一项**就是 R3 风险**: 如果 LDO 是 CE 高有效, CE 接 GND 会让 LDO 永远关断. 测出来"通"必须先做 §3.3 LDO 输出测试再决定是否飞线.

### 2.3 关键引脚连通性

| 信号 | 模组 Pin | 应通到 |
|---|---|---|
| KEY_1 (IO2) | 38 | SW1 一端 |
| LED_IN (IO42) | 35 | LED1 pin 4 (DIN) |
| SCL (IO20) | 14 | U4 pin 23 |
| SDA (IO47) | 24 | U4 pin 24 |
| INT (IO4) | 4 | U4 pin 11 (注意: 丝印 FSYNC) |
| CHRG (IO5) | 5 | U3 pin 1 |
| TXD0 (IO43) | 37 | U5 pin 2 |
| RXD0 (IO44) | 36 | U5 pin 3 |
| EN (RESET) | 3 | Q3 集电极 |
| BOOT (IO0) | 27 | Q2 集电极 |

任意一条不通 → 飞线修, 严重 → 重做板.

---

## 3. 阶段 1: 冒烟测试 (5 分钟, 极其重要)

### 3.1 第一次上电的正确姿势

1. **拔掉电池** (H2 不接), 只用 USB 供电, 这样万一 LDO 失控不会炸电池
2. **桌面准备好万用表 + 鼻子凑近闻焦糊味**
3. USB-A → USB-C 线接 USB1 (因为 R2: 不能用 USB-C → USB-C)
4. SW2 拨到关
5. 量 USB1 pin 2 → GND 应有 +5V
6. SW2 拨到开
7. **立即量 LDO1 pin 5 (VOUT)**:
   - **= 3.30 V ± 0.10 V** → ✅ 进入 §3.2
   - **= 0 V** → ⚠️ R3 触发! LDO 被 CE 关断, 立刻断电, 飞线把 LDO1 pin 3 改接 LDO1 pin 1 (VIN), 重做本步
   - **= 5 V (= VIN)** → LDO 短路坏了, 换片
   - **闻到糊味** → 立刻断电, 找冒烟器件

### 3.2 一旦 +3V3 出来, 测各点电压

| 测点 | 期望值 | 容差 | 实测 |
|---|---|---|---|
| USB1 pin 2 (VBUS) | 5.00 V | ± 0.25 V | _____ |
| LDO1 pin 1 (VIN) | 5.00 V | ± 0.25 V | _____ |
| **LDO1 pin 5 (VOUT)** | **3.30 V** | ± 0.10 V | _____ |
| MCU 模组 pin 2 (各 VDD) | 3.30 V | ± 0.10 V | _____ |
| U4 IMU pin 8 (VLOGIC) | 3.30 V | ± 0.10 V | _____ |
| U4 IMU pin 13 (VDD) | 3.30 V | ± 0.10 V | _____ |
| **U4 IMU pin 20 (CPOUT)** | **逐步爬升至 ~3 V** | 内部电荷泵升压 | _____ |
| U4 IMU pin 9 (AD0) | 0 V (= GND) | — | _____ |
| LED1 pin 1 (VDD) | 3.30 V | ± 0.10 V | _____ |
| U5 pin 16 (VCC) | 3.30 V | ± 0.10 V | _____ |
| U5 pin 4 (V3 内部 LDO) | 3.30 V | ± 0.10 V | _____ |
| U3 pin 4 (VCC = +5V) | 5.00 V | ± 0.25 V | _____ |

### 3.3 接电池后

1. 拔 USB
2. 把电池焊到 H2 母线 (注意 pin 1 = VBAT+, pin 2 = GND, **接反会炸 D1 或 LDO**)
3. SW2 拨到开
4. 量 LDO1 pin 5 应该仍是 **3.30 V** (Q1 P-MOSFET 切到电池路径)
5. 接回 USB → 应仍 3.30 V (Q1 切回 VBUS)
6. 用电流表串入 USB 测充电电流 → **~600 mA** ⚠️ R4: 关注电池温度

---

## 4. 阶段 2: I2C / IMU 单独验证 (烧最小 sketch, 不要烧完整固件)

> 阶段 2 全部通过后才进入阶段 3. 中间任意失败先修, 不要继续往下烧.

### 4.1 写一个 I2C scanner sketch

```cpp
#include <Arduino.h>
#include <Wire.h>
#include "board_config.h"

void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(cw::board::kPinI2cSda, cw::board::kPinI2cScl);  // = (47, 20)
  Wire.setClock(cw::board::kI2cClockHz);                       // = 400 kHz
}

void loop() {
  Serial.println("[scan] start");
  for (uint8_t addr = 1; addr < 127; ++addr) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  found 0x%02X\n", addr);
    }
  }
  Serial.println("[scan] done");
  delay(2000);
}
```

放到 `Software/src/main.cpp` 临时替换原 `setup/loop` (跑完测试再 git checkout 回滚), 或者新建一个 PIO env.

**通过标准**: 看到 `found 0x68` (AD0 = GND 时 InvenSense 系列默认地址).

### 4.2 I2C 失败诊断

| 现象 | 可能原因 | 排查 |
|---|---|---|
| `[scan] done` 全程 0 found | SDA/SCL 没上拉, 或硬件未连通 | 1. 万用表测 SDA / SCL 静态电压, 应接近 +3V3; **远低于 → 飞 4.7K 上拉 (R1 风险触发)**. 2. 阶段 0.3 已经测过连通, 这里再确认一次. 3. 示波器看 SCL 是否有 400kHz 时钟波形 (有 → MCU 端 OK, 看 SDA; 无 → MCU `Wire.begin` 引脚不对, 检查 board_config.h) |
| 看到 `found 0x69` | AD0 错接到 +3V3 而非 GND | 飞线把 U4 pin 9 改接 GND |
| 看到 `found 0x68` 但下一步读 WHOAMI 失败 | I2C 通了但 IC 不响应寄存器 | 见 §4.3 |

### 4.3 读 WHOAMI 确认 IC 实际型号

```cpp
#include <Wire.h>
#include "board_config.h"

void setup() {
  Serial.begin(115200);
  Wire.begin(cw::board::kPinI2cSda, cw::board::kPinI2cScl);
  Wire.setClock(cw::board::kI2cClockHz);
  delay(500);

  Wire.beginTransmission(0x68);
  Wire.write(0x75);   // WHO_AM_I 寄存器
  Wire.endTransmission(false);
  Wire.requestFrom(0x68, (uint8_t)1);
  if (Wire.available()) {
    uint8_t whoami = Wire.read();
    Serial.printf("WHOAMI = 0x%02X\n", whoami);
    switch (whoami) {
      case 0x68: Serial.println("=> MPU-6050");                    break;
      case 0x71: Serial.println("=> MPU-9250");                    break;
      case 0x12: Serial.println("=> ICM-20602");                   break;
      case 0x98: Serial.println("=> ICM-20689");                   break;
      case 0xEA: Serial.println("=> ICM-20948 (incompatible!)");   break;
      default:   Serial.printf("=> UNKNOWN (0x%02X)\n", whoami);   break;
    }
  } else {
    Serial.println("WHOAMI read failed");
  }
}
void loop() {}
```

**通过标准**: WHOAMI = 0x68 (MPU-6050) 或 0x71 (MPU-9250) → 当前 `electroniccats/MPU6050` 库可用, 直接进阶段 3.

**不通过的处理**:
- WHOAMI = 0x12 (ICM-20602) / 0x98 (ICM-20689): 部分寄存器地址不同, 当前库勉强可用但读 IMU 数据会偏; 看运行情况再决定是否换库
- WHOAMI = 0xEA (ICM-20948): **必须换库** (Sparkfun ICM-20948), `lib/imu/mpu6050_imu.{h,cpp}` 整个改写
- WHOAMI = 其他 / 读失败: 见 §4.4

### 4.4 IMU 读不到 / 数据异常诊断

1. **U4 pin 20 CPOUT 上的 C7 = 2.2nF 必须焊接**: InvenSense 内部电荷泵需要这颗电容才能启动; 没焊整片 IC 不响应 (I2C 都失败)
2. U4 pin 13 VDD 必须 = +3V3, pin 25 EP (中间散热焊盘) 必须接 GND
3. U4 pin 6 / 7 (AUX_DA / AUX_CL) 没用, 应该 NC; 错接到其他网络会让内部主 I2C 死锁
4. IMU 焊歪 / 焊盘虚焊 → 重焊; 用助焊剂 + 热风枪重新植球

---

## 5. 阶段 3: 按键 + LED 单独验证

### 5.1 按键测试

```cpp
#include <Arduino.h>
#include "board_config.h"

void setup() {
  Serial.begin(115200);
  pinMode(cw::board::kPinKey1, INPUT_PULLUP);   // = IO2
}
void loop() {
  Serial.printf("KEY_1 = %d\n", digitalRead(cw::board::kPinKey1));
  delay(200);
}
```

**通过标准**: 不按 = 1, 按住 = 0, 切换稳定无抖动 (软件没消抖也不抖动表示 R2 = 10K 上拉够强).

### 5.2 WS2812 LED 测试

```cpp
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "board_config.h"

Adafruit_NeoPixel strip(cw::board::kLed1Count, cw::board::kPinLed1Data,
                        NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.setBrightness(60);
}
void loop() {
  strip.setPixelColor(0, 255, 0, 0);   strip.show(); delay(500);  // R
  strip.setPixelColor(0,   0, 255, 0); strip.show(); delay(500);  // G
  strip.setPixelColor(0,   0,   0, 255); strip.show(); delay(500); // B
}
```

**通过标准**: LED1 依次显示红 / 绿 / 蓝, 每 500ms 切换. 颜色错误 → 改 `NEO_GRB` 为 `NEO_RGB` 试一次 (国产兼容芯片偶有色序差异).

**LED 全程不亮的诊断**:
1. 量 LED1 pin 1 (VDD) 应该 = +3V3
2. 量 LED1 pin 4 (DIN) 是否有方波 (示波器, 触发 1V); 无 → MCU 端 IO42 没驱动, 检查 `kPinLed1Data` 与板子是否一致
3. 检查 R1 = 10K (DIN 上拉) 是否焊接; 缺就飞一颗

---

## 6. 阶段 4: 充电状态与 USB 自动复位

### 6.1 充电状态读取

```cpp
#include <Arduino.h>
#include "board_config.h"
void setup() {
  Serial.begin(115200);
  pinMode(cw::board::kPinChargeStat, INPUT_PULLUP);   // = IO5
}
void loop() {
  Serial.printf("CHRG = %d  (LOW=charging, HIGH=full/no-USB)\n",
                digitalRead(cw::board::kPinChargeStat));
  delay(500);
}
```

**通过标准**:
- 接 USB + 电池电量 < 4.2V → CHRG = 0, LED2 (红色) 亮
- 充满 / 拔 USB → CHRG = 1, LED2 灭

### 6.2 USB 自动复位电路

不需要单独写 sketch, 直接 `pio run -t upload` 烧任意程序观察行为:
- esptool 输出能看到 `Hard resetting via RTS pin...` 且烧录后立即运行 → ✅ Q2 / Q3 正常
- 烧录前需要手动按 BOOT 键 → Q2 (BOOT 控制) 焊接问题
- 烧录后 MCU 不复位需要插拔 USB → Q3 (RESET 控制) 焊接问题

---

## 7. 阶段 5: 烧完整固件跑端到端业务

前 4 个阶段全部通过后, 才进入完整固件烧录.

### 7.1 烧录

```bash
cd Software
pio run                        # 编译, 看 SUCCESS
pio run -t upload              # 烧录
pio device monitor -b 115200   # 串口监控
```

固件路径: `Software/.pio/build/cyberwand/firmware.bin`

### 7.2 期望的启动日志序列

```
[system] loop Priority: 1
[system] loop Priority: 3
MPU6050 connection successful           ← 即便 IC 是 ICM 兼容, MPU6050 库基于 0x68 测连接也会过
[ble] init done
```

### 7.3 业务功能验证清单

- [ ] **按下按键** → 串口看到 `[main] capture returned: buf=0x... n=NN reason=0`, n 与按住时长大致成正比 (10ms / 帧)
- [ ] **录制中 LED**: 按下 LED 红色常亮, 松开熄灭
- [ ] **松开按键** → 串口打印 `[main] capture done: NN frames` 或 `gesture too short, discarded` (n < 30)
- [ ] **手势识别**: 挥圆圈 → `[app] action type: 0` 或 `1` (`kCircle_Cw / kCircle_Aw`); 挥勾 → `[app] action type: 2` (`kCheck`); 挥叉 → `[app] action type: 3` 或 `4`
- [ ] **双击切模式**: 双击按键 → LED **蓝色快闪 2 秒** + 串口 `[main] mode -> Acquisition`; 再双击 → LED **绿色长亮 3 秒** + `[main] mode -> Application`
- [ ] **BLE 广播**: 用手机 nRF Connect 扫描看到外设名 (开发期 `Insta360 GPS Remote` / 开源版 `CyberWand`)
- [ ] **BLE 命令下发**: 连上相机后挥圆圈 → 串口 `[main] gesture circle -> cmd sent OK`

### 7.4 端到端失败诊断 (基于本固件特点)

| 现象 | 原因 | 排查 |
|---|---|---|
| 启动卡在 `MPU6050 connection failed` | I2C 通信失败 / IC 不是 6050 兼容 | 回到 §4.2; 如果 §4.3 WHOAMI 是 ICM-20948 必须换库 |
| 按键无反应, 串口无 `capture returned` 日志 | 按键焊接虚焊 / `kPinKey1` 不是 IO2 | 用 §5.1 sketch 单测; 不一致时改 `board_config.h` |
| 按下有 `capture returned` 但 n 永远 1~2 | 按键反弹 / 抖动严重 | 示波器看 KEY_1 波形, 加 0.1uF 到 GND |
| 手势识别永远 `kUnknown` | IMU 数据异常 / Resampler 输出全 0 | 双击进 Acquisition 模式, 串口看 6 通道原始数据是否合理 |
| LED 不亮 / 颜色错乱 | WS2812 时序问题 / 色序错 | 回到 §5.2; 改 `NEO_GRB` ↔ `NEO_RGB` |
| BLE 扫不到 | BLE init 失败 / 天线匹配差 | 看是否有 `[ble] init done` 日志; 远离金属物体重试 |

---

## 8. 长期测试与已知 v4.0 → v4.1 板级改进项

### 8.1 长期烧机 (24 小时)

接 USB 持续运行, 每 4 小时记录:
- 电池电压 (拔 USB 后量 H2 pin 1)
- 电池温度 (热成像 / 手摸)
- MCU 模组温度
- 是否复位过 (串口看是否有重启日志)

### 8.2 v4.1 板级改进建议 (汇总自 §1 风险表)

| 优先级 | 改进 | 影响 |
|---|---|---|
| 🔴 高 | I2C SDA/SCL 各加 4.7K 上拉到 +3V3 | 提高 I2C 总线稳定性, 消除 R1 风险 |
| 🔴 高 | USB-C CC1, CC2 各加 5.1K 下拉到 GND | 支持 USB-C → USB-C 线供电, 消除 R2 风险 |
| 🟡 中 | 验证 LDO 实际型号后, 决定 CE 接 VIN 还是保持 GND | 消除 R3 风险 |
| 🟡 中 | 加 VBAT 分压电路 (R'1=R'2=100K + 飞线到 IO6) | 实现电量监测, 消除 R6 风险 |
| 🟢 低 | R5 改 4.7 kΩ (250 mA 充电) 或换更大电池 | 延长电池寿命, 消除 R4 风险 |
| 🟢 低 | IMU pin 11/12 标号修正, 走线到正确的 INT 输出 | 消除 R5 风险, 启用 DRDY 中断 |

---

## 9. 文档索引

- 硬件设计文档 (BOM / 引脚 / 电路): `HardWare/cyberwand_hardware_v3.md` (v4.0)
- 原理图分块图: `enclosure/{充电,IMU,MCU,USB}.png`
- PCB 几何: `enclosure/DXF_PCB1_2026-05-01_AutoCAD2007.dxf`
- 软件硬件配置入口: `Software/include/board_config.h`
- 软件: `Software/src/main.cpp` + `Software/lib/{ble,button,led,imu,cnn}/`
- 固件清洁性脚本: `Software/scripts/verify_firmware_clean.sh`
- 单元测试: `Software/test/run.sh` (本机 g++ + CMake, 56 tests)
