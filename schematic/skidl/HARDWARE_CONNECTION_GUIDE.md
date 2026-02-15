# CyberWand v2.3 - 完整电路原理图连接指南

> **版本**: v2.3 | **日期**: 2026-02-14
> **网表**: `output/cyberwand_netlist.net`
> **总元件**: 66件 | **总网络**: 51个

---

## 一、电源子系统原理图

### 1.1 USB输入 → PTC保险丝 → ESD保护 → 滤波

```
                    USB Type-C 母座 (J2)
                    HRO TYPE-C-31-M-12
        ┌──────────────────────────────────────┐
        │ A4(VBUS)──┐                          │
        │ B4(VBUS)──┼──── 5V                   │
        │           │                          │
        │ A6(DP1)───┼──┐                       │
        │ B6(DP2)───┼──┤  USB_DP               │
        │           │  │                       │
        │ A7(DN1)───┼──┼──┐                    │
        │ B7(DN2)───┼──┼──┤ USB_DN             │
        │           │  │  │                    │
        │ A5(CC1)───┼──┼──┼──┐                 │
        │ B5(CC2)───┼──┼──┼──┼──┐              │
        │           │  │  │  │  │              │
        │ A1(GND)───┤  │  │  │  │              │
        │ B1(GND)───┤  │  │  │  │              │
        │A12(GND)───┼──┼──┼──┼──┼── GND        │
        │B12(GND)───┤  │  │  │  │              │
        │ S1(SHLD)──┘  │  │  │  │              │
        └──────────────┼──┼──┼──┼──────────────┘
                       │  │  │  │
    5V ────────────────┘  │  │  │
    │                     │  │  │
    │   ┌─────────────┐   │  │  │
    │   │  F1 (PTC)   │   │  │  │
    ├───┤1          2 ├───┤  │  │
    │   │ 500mA/15V   │   │  │  │
    │   └─────────────┘   │  │  │
    │                     │  │  │
    │             5V_PROT─┘  │  │
    │             │          │  │
    │   ┌─────────┼──────┐   │  │
    │   │C15      │      │   │  │
    │   │10uF  ┌──┘      │   │  │
    │   │1──┤├──2        │   │  │
    │   │  GND           │   │  │
    │   └────────────────┘   │  │
    │   ┌────────────────┐   │  │
    │   │C17             │   │  │
    │   │22uF  5V_PROT   │   │  │
    │   │1──┤├──2        │   │  │
    │   │  GND           │   │  │
    │   └────────────────┘   │  │
    │                        │  │
    │   USB_DP───────────────┘  │
    │   │                       │
    │   │  ┌──────────┐        │
    │   ├──┤1  R18    2├────┐   │
    │   │  │  22Ω     │    │   │
    │   │  └──────────┘    │   │
    │   │            USB_DP_INT │
    │   │                  │   │
    │   USB_DN─────────────┼───┘
    │   │                  │
    │   │  ┌──────────┐   │
    │   └──┤1  R19    2├──┐│
    │      │  22Ω     │  ││
    │      └──────────┘  ││
    │              USB_DN_INT
    │                  │  │
    │    USBLC6-2SC6 (U6) │
    │    SOT-23-6         │
    │   ┌─────────────────┤───────┐
    │   │                 │       │
    │   │ 6(IO1_2)────────┤       │
    │   │                 │       │
    │   │ 1(IO1_1)─── USB_DP_INT │
    │   │                         │
    │   │ 5(VBUS)──── 5V_PROT    │
    │   │                         │
    │   │ 3(IO2_1)─── USB_DN_INT │
    │   │                 │       │
    │   │ 4(IO2_2)────────┘       │
    │   │                         │
    │   │ 2(GND)───── GND        │
    │   └─────────────────────────┘
    │
    │           USB_DP_INT ────── ESP32 IO20 (Pin14)
    │           USB_DN_INT ────── ESP32 IO19 (Pin13)
    │
    │   ┌──────────┐     ┌──────────┐
    ├───┤1  R8    2├─GND │1  R9    2├─GND
    │   │  5.1KΩ   │     │  5.1KΩ   │
    │   └──────────┘     └──────────┘
    │   CC1(A5)─┘         CC2(B5)─┘
    │
   GND
```

### 1.2 TP4056 充电管理 + LED指示

```
                     TP4056 (U4)  SOIC-8
                ┌──────────────────────────┐
                │                          │
  GND ───────────┤ 1(TEMP)      8(CE) ├──── 5V_PROT
                │ ★TEMP接GND禁用!    │     (接VCC会阻止充电)
                │                          │
  R10(2KΩ)─┬───┤ 2(PROG)      7(CHRG)├──── CHRG_STATUS
  R10另一端─┤   │                          │
  GND ──────┘   │ 3(GND)      6(STDBY)├─── STDBY_STATUS
                │  │                       │
  5V_PROT ──────┤ 4(VCC)      5(BAT) ├──── VBAT
                │                          │
                └──────────────────────────┘
                   │                   │
                  GND                  │
                              ┌───────┤
                              │       │
                              │  ┌────┴────┐
                              │  │ C_BAT   │
                              │  │ 10uF    │
                              │  │1──┤├──2 │
                              │  │  GND    │
                              │  └─────────┘
                              │
                              VBAT

充电红色LED:                       充满绿色LED:
  5V_PROT                           5V_PROT
    │                                 │
  ┌─┴──────┐                        ┌─┴──────┐
  │1 R11  2│                        │1 R12  2│
  │ 1KΩ    │                        │ 1KΩ    │
  └────┬───┘                        └────┬───┘
       │                                 │
    ┌──┴──┐                           ┌──┴──┐
    │A  D4│ (红)                      │A  D5│ (绿)
    │  LED│                           │  LED│
    │K    │                           │K    │
    └──┬──┘                           └──┬──┘
       │                                 │
  CHRG_STATUS ── U4 Pin7            STDBY_STATUS ── U4 Pin6
  (充电时LOW→LED亮)                  (充满时LOW→LED亮)
```

### 1.3 电池 + 电源开关 + LDO

```
  锂电池 603040 (BT1)                 电源开关 (SW1) MSK-12C02
  ┌──────────────────┐             ┌────────────────────┐
  │  3.7V / 800mAh   │             │                    │
  │                  │     VBAT    │ 1(COM) ── VBAT     │
  │ 1(+) ────────────┼─────────────┤                    │
  │                  │             │ 2(NO) ─── VBAT_SW  │
  │ 2(-) ── GND     │             │                    │
  └──────────────────┘             │ 3(NC) ─── 悬空!   │
                                   └────────────────────┘
                                             │
                                          VBAT_SW
                                             │
               ┌───────────┐      ┌──────────┴───────────┐
               │ C14 10uF  │      │                      │
               │1──┤├──2   │      │  ME6211 (U5) SOT-23  │
               │VBAT_SW GND│      │                      │
               └───────────┘      │ 1(VIN) ── VBAT_SW   │
                                  │                      │
                                  │ 2(VOUT)── 3V3       │ ★Pin2是VOUT!
                                  │                      │
                                  │ 3(VSS) ── GND       │ ★Pin3是GND!
               ┌───────────┐      └──────────────────────┘
               │ C9 10uF   │                │
               │1──┤├──2   │              3V3
               │3V3    GND │
               └───────────┘
```

---

## 二、ESP32-S3 主控子系统原理图

```
                          3V3
                           │
                     ┌─────┴─────┐
                     │1  R1     2│
                     │  10KΩ     │
                     └─────┬─────┘
                           │           ┌───────────┐
                           ├───────────┤1 C_EN    2│
                           │           │  1uF   GND│
            ESP32-S3-WROOM-1N16R8 (U1) └───────────┘
     ┌─────────────────────────────────────────────────────┐
     │  3(EN) ─────────────┘                               │
     │                                                     │
     │  2(3V3) ─── 3V3                                    │
     │  1(GND1)─── GND                                    │
     │ 40(GND2)─── GND                                    │
     │ 41(EPAD)─── GND                                    │
     │                                                     │
     │  4(IO4) ─── I2C_SDA ──→ MPU6050 Pin24(SDA)        │
     │  5(IO5) ─── I2C_SCL ──→ MPU6050 Pin23(SCL)        │
     │  6(IO6) ─── MPU6050_INT ←─ MPU6050 Pin12(INT)     │
     │                                                     │
     │  7(IO7) ─── I2S_SCK_MCU ──[R15 33Ω]──→ INMP441 Pin3(SCK)
     │  8(IO15)─── I2S_SD ←──────────────── INMP441 Pin4(SD)
     │  9(IO16)─── I2S_WS_MCU ──[R16 33Ω]──→ INMP441 Pin5(WS)
     │                                                     │
     │ 17(IO9) ─── SPI_SCK_MCU ─[R13 33Ω]─→ LCD Pin3 + SD Pin5
     │ 21(IO13)─── SPI_MOSI_MCU ─[R14 33Ω]─→ LCD Pin4 + SD Pin7
     │ 20(IO12)─── SPI_MISO ←───────────── SD Pin8(MISO)  │
     │ 19(IO11)─── LCD_DC ──→ LCD Pin6(DC)                │
     │ 22(IO14)─── SPI_CS_LCD ──→ LCD Pin7(CS)            │
     │ 18(IO10)─── SPI_CS_SD ──→ SD Pin2(CS)              │
     │ 10(IO17)─── LCD_RST ──→ LCD Pin5(RES)              │
     │                                                     │
     │ 24(IO47)─── UART_TX ──[R20 1KΩ]──→ DFPlayer Pin2(RX)
     │ 25(IO48)─── UART_RX ←──────────── DFPlayer Pin3(TX)│
     │ 26(IO45)─── DFPLAYER_BUSY ←─────── DFPlayer Pin16  │
     │                                                     │
     │ 13(IO19)─── USB_DN_INT ←── USBLC6 ←── Type-C D-   │
     │ 14(IO20)─── USB_DP_INT ←── USBLC6 ←── Type-C D+   │
     │                                                     │
     │ 23(IO21)─── LED_DATA_MCU ──[R17 100Ω]──→ 74AHCT125│
     │                                                     │
     │ 12(IO8) ─── KEY_MODE ──→ SW2                       │
     │ 15(IO3) ─── KEY_SELECT ──→ SW3                     │
     │ 27(IO0) ─── KEY_PLAY ──→ SW4                       │
     │                                                     │
     │ 16(IO46)─── [R7 10KΩ] ──→ GND                     │
     │                                                     │
     │ 28(IO35)─── NC (PSRAM)                              │
     │ 29(IO36)─── NC (PSRAM)                              │
     │ 30(IO37)─── NC (PSRAM)                              │
     └─────────────────────────────────────────────────────┘

去耦电容 (紧贴3V3引脚):
  3V3 ─┤C1 100nF├─ GND
  3V3 ─┤C2 100nF├─ GND
  3V3 ─┤C3 10uF ├─ GND
```

---

## 三、MPU6050 子系统原理图

```
             3V3                        3V3
              │                          │
        ┌─────┴─────┐             ┌──────┴─────┐
        │1  R2     2│             │1  R3      2│
        │  4.7KΩ    │             │  4.7KΩ     │
        └─────┬─────┘             └──────┬─────┘
              │ I2C_SDA                  │ I2C_SCL
              │                          │
         MPU6050 (U2) QFN-24             │
     ┌────────┼──────────────────────────┼──────────────┐
     │        │                          │              │
     │ 13(VDD) ── 3V3                                   │
     │                                                  │
     │  8(VLOGIC) ── 3V3                                │
     │                                                  │
     │ 18(GND) ── GND                                   │
     │                                                  │
     │ 24(SDA) ── I2C_SDA ──────────────→ ESP32 Pin4(IO4)
     │                                                  │
     │ 23(SCL) ── I2C_SCL ──────────────→ ESP32 Pin5(IO5)
     │                                                  │
     │  9(AD0) ── GND  (I2C地址=0x68)                   │
     │                                                  │
     │ 12(INT) ── MPU6050_INT ──────────→ ESP32 Pin6(IO6)
     │                                                  │
     │  1(CLKIN)── GND  ★必须接地                       │
     │                                                  │
     │ 11(FSYNC)── GND  ★必须接地                       │
     │                                                  │
     │ 20(CPOUT)── C_CP(2.2nF) ── GND  ★电荷泵必须     │
     │                                                  │
     │ 10(REGOUT)── C_REG(100nF)── GND ★稳压器必须     │
     │                                                  │
     │ 19(RESV) ── NC (保留不接)                         │
     │  6(AUX_DA)── NC                                   │
     │  7(AUX_CL)── NC                                   │
     │  2,3,4,5,14,15,16,17,21,22 ── NC                 │
     └──────────────────────────────────────────────────┘

     ┌───────────┐    ┌───────────┐    ┌───────────┐
     │ C4 100nF  │    │C_CP 2.2nF │    │C_REG 100nF│
     │VDD──┤├─GND│    │CPOUT┤├─GND│    │REGOUT┤├GND│
     └───────────┘    └───────────┘    └───────────┘
```

---

## 四、SPI总线子系统 (LCD + SD卡)

```
  ESP32                  33Ω阻尼              HS20S010B LCD (LCD1)
 ┌──────┐             ┌─────────┐           ┌─────────────────────┐
 │Pin17 │ SPI_SCK_MCU │1 R13  2│ SPI_SCK   │                     │
 │(IO9) ├─────────────┤  33Ω   ├───────┬───┤ 3(SCL) ── SPI_SCK  │
 │      │             └─────────┘       │   │                     │
 │Pin21 │ SPI_MOSI_MCU┌─────────┐      │   │ 4(SDA) ── SPI_MOSI │
 │(IO13)├─────────────┤1 R14  2├───┬───┼───┤                     │
 │      │             │  33Ω   │   │   │   │ 5(RES) ── LCD_RST   │
 │      │             └─────────┘   │   │   │   │                 │
 │Pin20 │ SPI_MISO         │       │   │   │ 6(DC)  ── LCD_DC    │
 │(IO12)├──────────┐       │       │   │   │   │                 │
 │      │          │       │       │   │   │ 7(CS)  ── SPI_CS_LCD│
 │Pin19 │ LCD_DC   │       │       │   │   │   │                 │
 │(IO11)├──────────┼───────┼───────┼───┼───┤ 8(BLK) ── 3V3      │
 │      │          │       │       │   │   │                     │
 │Pin22 │SPI_CS_LCD│       │       │   │   │ 2(VCC) ── 3V3      │
 │(IO14)├──────────┼───────┼───────┼───┼───┤ 1(GND) ── GND      │
 │      │          │       │       │   │   │                     │
 │Pin10 │ LCD_RST  │       │       │   │   │ 9(FSO) ── NC       │
 │(IO17)├──────────┼───────┼───────┼───┼───┤10(FCS) ── NC       │
 │      │          │       │       │   │   └─────────────────────┘
 │Pin18 │SPI_CS_SD │       │       │   │
 │(IO10)├──────┐   │       │       │   │  去耦: C5(100nF)+C6(10uF)
 │      │      │   │       │       │   │  3V3──┤├──GND  3V3──┤├──GND
 └──────┘      │   │       │       │   │
               │   │       │       │   │
               │   │  MicroSD卡座 (J1) │
               │   │  Hirose DM3AT     │
               │   │ ┌─────────────────┤──────┐
               │   │ │                 │      │
               │   └─┤ 8(MISO)── SPI_MISO    │
               │     │                        │
               │     │ 5(SCK) ── SPI_SCK ─────┘ (共享)
               │     │                        │
               └─────┤ 2(CS)  ── SPI_CS_SD   │
                     │                        │
                     │ 7(MOSI)── SPI_MOSI ───── (共享)
                     │                        │
                     │ 4(VCC) ── 3V3          │
                     │ 3(GND) ── GND          │
                     │ 1(SHLD)── GND          │
                     │ 9(CD)  ── NC           │
                     └────────────────────────┘
```

---

## 五、DFPlayer音频子系统原理图

```
   ESP32                              DFPlayer Mini (U3)
  ┌──────┐                         ┌──────────────────────────┐
  │Pin24 │  UART_TX   ┌────────┐  │                          │
  │(IO47)├────────────┤1 R20  2├──┤ 2(RX) ← UART_TX_PROT    │
  │      │            │  1KΩ   │  │                          │
  │Pin25 │  UART_RX   └────────┘  │ 3(TX) ── UART_RX        │
  │(IO48)├────────────────────────┤                          │
  │      │                        │16(BUSY)── DFPLAYER_BUSY  │
  │Pin26 │  DFPLAYER_BUSY         │                          │
  │(IO45)├────────────────────────┤ 1(VCC) ── 3V3            │
  └──────┘                        │ 7(GND) ── GND            │
                                  │                          │
                                  │ 8(SPK1)──┐               │
                                  │          │  扬声器 (LS1)  │
                                  │ 9(SPK2)──┤  8Ω 0.5W     │
                                  │          │               │
                                  └──────────┼───────────────┘
                                             │
                                  ┌──────────┼──────────┐
                                  │ C7 10uF  │C8 100nF  │
                                  │3V3┤├GND  │3V3┤├GND  │
                                  └──────────┴──────────┘
```

---

## 六、INMP441 麦克风子系统原理图

```
  ESP32                          INMP441 (MIC1)
 ┌──────┐                     ┌──────────────────┐
 │Pin7  │ I2S_SCK_MCU         │                  │
 │(IO7) ├──────┐              │ 1(VDD)── 3V3    │
 │      │  ┌───┴───────┐     │                  │
 │      │  │1 R15     2│     │ 2(GND)── GND    │
 │      │  │  33Ω      │     │                  │
 │      │  └───────┬───┘     │ 3(SCK)── I2S_SCK│
 │      │    I2S_SCK──────────┤                  │
 │Pin8  │                     │ 4(SD) ── I2S_SD │
 │(IO15)├─── I2S_SD ──────────┤                  │
 │      │                     │ 5(WS) ── I2S_WS │
 │Pin9  │ I2S_WS_MCU          │                  │
 │(IO16)├──────┐              │ 6(L_R)── GND    │
 │      │  ┌───┴───────┐     └──────────────────┘
 │      │  │1 R16     2│
 │      │  │  33Ω      │     去耦: C10(100nF)
 │      │  └───────┬───┘     3V3──┤├──GND
 │      │    I2S_WS──┘
 └──────┘
```

---

## 七、WS2812B LED + 电平转换子系统原理图

```
  ESP32          100Ω串联           SN74AHCT125 (U7) SOIC-14
 ┌──────┐     ┌──────────┐     ┌───────────────────────────────────┐
 │Pin23 │     │1 R17    2│     │                                   │
 │(IO21)├─────┤  100Ω    ├─────┤ 2(1A)  ← LED_DATA_BUF (3.3V)    │
 │      │     └──────────┘     │                                   │
 └──────┘   LED_DATA_MCU       │ 3(1Y)  → LED_DATA_5V (5V) ──┐   │
                               │                               │   │
                               │ 1(1OE) ── GND (使能)         │   │
                               │ 4(2OE) ── GND (使能)         │   │
                               │ 5(2A)  ── GND                │   │
                               │ 9(3OE) ── 5V_PROT (禁用)     │   │
                               │ 8(3A)  ── GND                │   │
                               │12(4OE) ── 5V_PROT (禁用)     │   │
                               │11(4A)  ── GND                │   │
                               │                               │   │
                               │14(VCC) ── 5V_PROT            │   │
                               │ 7(GND) ── GND                │   │
                               └───────────────────────────────┘   │
                                                                   │
                               C16(100nF): 5V_PROT──┤├──GND       │
                                                                   │
                                          LED_DATA_5V ─────────────┘
                                                │
             ┌──────────────────────────────────┘
             │
             ▼ DIN
   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │  D1 WS2812B  │      │  D2 WS2812B  │      │  D3 WS2812B  │
   │              │      │              │      │              │
   │1(VDD)─5V_PROT│      │1(VDD)─5V_PROT│      │1(VDD)─5V_PROT│
   │3(GND)─GND   │      │3(GND)─GND   │      │3(GND)─GND   │
   │4(DIN)←──────│      │4(DIN)←──────│      │4(DIN)←──────│
   │2(DOUT)──────→│      │2(DOUT)──────→│      │2(DOUT)── NC │
   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
          │                     │                     │
   C11(100nF)             C12(100nF)            C13(100nF)
   5V_PROT┤├GND           5V_PROT┤├GND          5V_PROT┤├GND
```

---

## 八、按键子系统原理图 (×3组相同结构)

```
按键1 (模式选择):                按键2 (手势选择):                按键3 (播放/确认):

        3V3                            3V3                            3V3
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │1  R4     2│                  │1  R5     2│                  │1  R6     2│
   │  10KΩ     │                  │  10KΩ     │                  │  10KΩ     │
   └─────┬─────┘                  └─────┬─────┘                  └─────┬─────┘
         │ KEY_MODE                     │ KEY_SELECT                   │ KEY_PLAY
         ├───── ESP32 Pin12(IO8)        ├──── ESP32 Pin15(IO3)        ├──── ESP32 Pin27(IO0)
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │1 C18     2│                  │1 C19     2│                  │1 C20     2│
   │ 100nF  GND│                  │ 100nF  GND│                  │ 100nF  GND│
   └───────────┘                  └───────────┘                  └───────────┘
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │1  SW2    2│                  │1  SW3    2│                  │1  SW4    2│
   │  按键     │                  │  按键     │                  │  按键     │
   └─────┬─────┘                  └─────┬─────┘                  └─────┬─────┘
         │                              │                              │
        GND                            GND                            GND
```

---

## 九、完整引脚对引脚连线表

### ESP32-S3 Pin → 目标

| ESP32引脚 | 物理Pin | 网络名 | → 中间元件 | → 目标芯片.引脚 |
|-----------|---------|--------|-----------|----------------|
| IO0 | 27 | KEY_PLAY | R6(10K)→3V3, C20(100nF)→GND | SW4.Pin1 |
| IO3 | 15 | KEY_SELECT | R5(10K)→3V3, C19(100nF)→GND | SW3.Pin1 |
| IO4 | 4 | I2C_SDA | R2(4.7K)→3V3 | U2(MPU6050).Pin24 |
| IO5 | 5 | I2C_SCL | R3(4.7K)→3V3 | U2(MPU6050).Pin23 |
| IO6 | 6 | MPU6050_INT | 直连 | U2(MPU6050).Pin12 |
| IO7 | 7 | I2S_SCK_MCU | R15(33Ω) | MIC1(INMP441).Pin3 |
| IO8 | 12 | KEY_MODE | R4(10K)→3V3, C18(100nF)→GND | SW2.Pin1 |
| IO9 | 17 | SPI_SCK_MCU | R13(33Ω) | LCD1.Pin3 + J1.Pin5 |
| IO10 | 18 | SPI_CS_SD | 直连 | J1(SD).Pin2 |
| IO11 | 19 | LCD_DC | 直连 | LCD1.Pin6 |
| IO12 | 20 | SPI_MISO | 直连 | J1(SD).Pin8 |
| IO13 | 21 | SPI_MOSI_MCU | R14(33Ω) | LCD1.Pin4 + J1.Pin7 |
| IO14 | 22 | SPI_CS_LCD | 直连 | LCD1.Pin7 |
| IO15 | 8 | I2S_SD | 直连 | MIC1(INMP441).Pin4 |
| IO16 | 9 | I2S_WS_MCU | R16(33Ω) | MIC1(INMP441).Pin5 |
| IO17 | 10 | LCD_RST | 直连 | LCD1.Pin5 |
| IO19 | 13 | USB_DN_INT | R19(22Ω)+U6(ESD) | J2(USB).DN1,DN2 |
| IO20 | 14 | USB_DP_INT | R18(22Ω)+U6(ESD) | J2(USB).DP1,DP2 |
| IO21 | 23 | LED_DATA_MCU | R17(100Ω)→U7(74AHCT125) | D1(WS2812B).Pin4 |
| IO45 | 26 | DFPLAYER_BUSY | 直连 | U3(DFPlayer).Pin16 |
| IO46 | 16 | (下拉) | R7(10K)→GND | - |
| IO47 | 24 | UART_TX | R20(1KΩ) | U3(DFPlayer).Pin2 |
| IO48 | 25 | UART_RX | 直连 | U3(DFPlayer).Pin3 |
| EN | 3 | (复位) | R1(10K)→3V3, C_EN(1uF)→GND | - |
| 3V3 | 2 | 3V3 | C1(100nF),C2(100nF),C3(10uF)→GND | - |
| GND1 | 1 | GND | - | - |
| GND2 | 40 | GND | - | - |
| EPAD | 41 | GND | - | - |

### 电源网络连线表

| 网络名 | 来源 | 连接到 (芯片.引脚) |
|--------|------|-------------------|
| 5V | J2.A4, J2.B4 | F1.Pin1 |
| 5V_PROT | F1.Pin2 | U4.Pin4(VCC), U4.Pin8(CE), U6.Pin5(VBUS), U7.Pin14(VCC), U7.Pin9(3OE), U7.Pin12(4OE), D1.Pin1(VDD), D2.Pin1(VDD), D3.Pin1(VDD), C15.1, C17.1, C16.1, C11.1, C12.1, C13.1, R11.1, R12.1 |
| VBAT | U4.Pin5(BAT), BT1.Pin1(+) | SW1.Pin1(COM), C_BAT.1 |
| VBAT_SW | SW1.Pin2(NO) | U5.Pin1(VIN), C14.1 |
| 3V3 | U5.Pin3(VOUT) | U1.Pin2, U2.Pin13(VDD), U2.Pin8(VLOGIC), LCD1.Pin2(VCC), LCD1.Pin8(BLK), J1.Pin4(VCC), U3.Pin1(VCC), MIC1.Pin1(VDD), R1.2, R2.2, R3.2, R4.2, R5.2, R6.2, C1.1, C2.1, C3.1, C4.1, C5.1, C6.1, C7.1, C8.1, C9.1, C10.1 |
| GND | 系统共地 | 所有芯片GND引脚, 所有电容Pin2, U4.Pin1(TEMP★), U2.Pin9(AD0), U2.Pin1(CLKIN), U2.Pin11(FSYNC), MIC1.Pin6(L_R), U7.Pin7, U7.Pin1(1OE), U7.Pin4(2OE), U7.Pin5(2A), U7.Pin8(3A), U7.Pin11(4A), R7.2, R8.2, R9.2, R10.2, J1.Pin1(SHLD), J1.Pin3 |

### 信号网络连线表

| 网络名 | Pin-A (起点) | Pin-B (终点) | 中间元件 |
|--------|-------------|-------------|---------|
| I2C_SDA | U1.Pin4(IO4) | U2.Pin24(SDA) | R2(4.7K)→3V3 |
| I2C_SCL | U1.Pin5(IO5) | U2.Pin23(SCL) | R3(4.7K)→3V3 |
| MPU6050_INT | U2.Pin12(INT) | U1.Pin6(IO6) | - |
| SPI_SCK_MCU | U1.Pin17(IO9) | R13.Pin1 | - |
| SPI_SCK | R13.Pin2 | LCD1.Pin3(SCL), J1.Pin5(SCK) | - |
| SPI_MOSI_MCU | U1.Pin21(IO13) | R14.Pin1 | - |
| SPI_MOSI | R14.Pin2 | LCD1.Pin4(SDA), J1.Pin7(MOSI) | - |
| SPI_MISO | J1.Pin8(MISO) | U1.Pin20(IO12) | - |
| SPI_CS_LCD | U1.Pin22(IO14) | LCD1.Pin7(CS) | - |
| SPI_CS_SD | U1.Pin18(IO10) | J1.Pin2(CS) | - |
| LCD_DC | U1.Pin19(IO11) | LCD1.Pin6(DC) | - |
| LCD_RST | U1.Pin10(IO17) | LCD1.Pin5(RES) | - |
| I2S_SCK_MCU | U1.Pin7(IO7) | R15.Pin1 | - |
| I2S_SCK | R15.Pin2 | MIC1.Pin3(SCK) | - |
| I2S_SD | MIC1.Pin4(SD) | U1.Pin8(IO15) | - |
| I2S_WS_MCU | U1.Pin9(IO16) | R16.Pin1 | - |
| I2S_WS | R16.Pin2 | MIC1.Pin5(WS) | - |
| UART_TX | U1.Pin24(IO47) | R20.Pin1 | - |
| UART_TX_PROT | R20.Pin2 | U3.Pin2(RX) | - |
| UART_RX | U3.Pin3(TX) | U1.Pin25(IO48) | - |
| DFPLAYER_BUSY | U3.Pin16(BUSY) | U1.Pin26(IO45) | - |
| USB_DP | J2.A6(DP1), J2.B6(DP2) | R18.Pin1 | - |
| USB_DP_INT | R18.Pin2 | U6.Pin1(IO1_1), U6.Pin6(IO1_2), U1.Pin14(IO20) | - |
| USB_DN | J2.A7(DN1), J2.B7(DN2) | R19.Pin1 | - |
| USB_DN_INT | R19.Pin2 | U6.Pin3(IO2_1), U6.Pin4(IO2_2), U1.Pin13(IO19) | - |
| LED_DATA_MCU | U1.Pin23(IO21) | R17.Pin1 | - |
| LED_DATA_BUF | R17.Pin2 | U7.Pin2(1A) | - |
| LED_DATA_5V | U7.Pin3(1Y) | D1.Pin4(DIN) | - |
| (D1→D2) | D1.Pin2(DOUT) | D2.Pin4(DIN) | - |
| (D2→D3) | D2.Pin2(DOUT) | D3.Pin4(DIN) | - |
| KEY_MODE | U1.Pin12(IO8) | R4.1, SW2.1, C18.1 | R4.2→3V3, SW2.2→GND, C18.2→GND |
| KEY_SELECT | U1.Pin15(IO3) | R5.1, SW3.1, C19.1 | R5.2→3V3, SW3.2→GND, C19.2→GND |
| KEY_PLAY | U1.Pin27(IO0) | R6.1, SW4.1, C20.1 | R6.2→3V3, SW4.2→GND, C20.2→GND |
| CHRG_STATUS | U4.Pin7(CHRG) | D4.K(阴极) | R11(1K): 5V_PROT→D4.A |
| STDBY_STATUS | U4.Pin6(STDBY) | D5.K(阴极) | R12(1K): 5V_PROT→D5.A |
| (PROG) | U4.Pin2(PROG) | R10.Pin1 | R10.2→GND |
| (CC1) | J2.A5(CC1) | R8.Pin1 | R8.2→GND |
| (CC2) | J2.B5(CC2) | R9.Pin1 | R9.2→GND |

---

*v2.2 所有引脚编号严格按各芯片数据手册。可作为KiCad绘制原理图的完整参考。*
