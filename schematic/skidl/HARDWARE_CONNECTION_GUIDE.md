# CyberWand v2.3 - 完整电路原理图连接指南

> **版本**: v2.3 | **日期**: 2026-02-14
> **网表**: `output/cyberwand_netlist.net`
> **总元件**: 66件 | **总网络**: 51个
> 
> **重要**: 本文档中所有连接关系均已按照**封装引脚标号**标注，格式为 `U1.Pin4(IO4) → U2.Pin24(SDA)`，可直接用于PCB布局和原理图绘制。

---

## 一、电源子系统原理图

### 1.1 USB输入 → PTC保险丝 → ESD保护 → 滤波

```
                    USB Type-C 母座 (J2)
                    TYPE-C 16PIN 2MD(073)
                    深圳市首韩科技有限公司
        ┌──────────────────────────────────────┐
        │ Pin2(VBUS1)──┐                       │
        │Pin11(VBUS2)──┼──── 5V                │
        │              │                       │
        │ Pin6(DP1)────┼──┐                    │
        │ Pin8(DP2)────┼──┤  USB_DP            │
        │              │  │                    │
        │ Pin7(DN1)────┼──┼──┐                 │
        │ Pin5(DN2)────┼──┼──┤ USB_DN          │
        │              │  │  │                 │
        │ Pin4(CC1)────┼──┼──┼──┐              │
        │Pin10(CC2)────┼──┼──┼──┼──┐           │
        │              │  │  │  │  │           │
        │ Pin1(GND1)───┤  │  │  │  │           │
        │Pin12(GND2)───┤  │  │  │  │           │
        │Pin13(SHL1)───┼──┼──┼──┼──┼── GND    │
        │Pin14(SHL2)───┤  │  │  │  │           │
        │ Pin3(SBU2)───┘  │  │  │  │           │
        │ Pin9(SBU1)──────┘  │  │  │           │
        └────────────────────┼──┼──┼───────────┘
                              │  │  │
    5V ───────────────────────┘  │  │
    │                        │  │  │
    │   ┌─────────────┐      │  │  │
    │   │  F1 (PTC)   │      │  │  │
    ├───┤Pin1      Pin2├──────┤  │  │
    │   │ 500mA/15V   │      │  │  │
    │   └─────────────┘      │  │  │
    │                        │  │  │
    │             5V_PROT────┘  │  │
    │             │            │  │
    │   ┌─────────┼──────┐     │  │
    │   │C15      │      │     │  │
    │   │10uF  ┌──┘      │     │  │
    │   │Pin1──┤├──Pin2  │     │  │
    │   │  GND           │     │  │
    │   └────────────────┘     │  │
    │   ┌────────────────┐     │  │
    │   │C17             │     │  │
    │   │22uF  5V_PROT   │     │  │
    │   │Pin1──┤├──Pin2  │     │  │
    │   │  GND           │     │  │
    │   └────────────────┘     │  │
    │                          │  │
    │   USB_DP──────────────────┘  │
    │   │                         │
    │   │  ┌──────────┐          │
    │   ├──┤Pin1 R18 Pin2├────┐    │
    │   │  │  22Ω     │    │    │
    │   │  └──────────┘    │    │
    │   │            USB_DP_INT │
    │   │                  │    │
    │   USB_DN─────────────┼────┘
    │   │                  │
    │   │  ┌──────────┐   │
    │   └──┤Pin1 R19 Pin2├──┐│
    │      │  22Ω     │  ││
    │      └──────────┘  ││
    │              USB_DN_INT
    │                  │  │
    │    USBLC6-2SC6 (U6) │
    │    SOT-23-6         │
    │   ┌─────────────────┤───────┐
    │   │                 │       │
    │   │ Pin6(IO1_2)─────┤       │
    │   │                 │       │
    │   │ Pin1(IO1_1)─── USB_DP_INT│
    │   │                         │
    │   │ Pin5(VBUS)──── 5V_PROT │
    │   │                         │
    │   │ Pin3(IO2_1)─── USB_DN_INT│
    │   │                 │       │
    │   │ Pin4(IO2_2)─────┘       │
    │   │                         │
    │   │ Pin2(GND)───── GND      │
    │   └─────────────────────────┘
    │
    │           USB_DP_INT ────── U1.Pin14(IO20)
    │           USB_DN_INT ────── U1.Pin13(IO19)
    │
    │   ┌──────────┐     ┌──────────┐
    ├───┤Pin1 R8 Pin2├─GND │Pin1 R9 Pin2├─GND
    │   │  5.1KΩ   │     │  5.1KΩ   │
    │   └──────────┘     └──────────┘
    │   CC1(PinA5)─┘      CC2(PinB5)─┘
    
连接关系:
  J2.Pin2(VBUS1) + J2.Pin11(VBUS2) → 5V → F1.Pin1 → F1.Pin2 → 5V_PROT
  J2.Pin6(DP1) + J2.Pin8(DP2) → USB_DP → R18.Pin1 → R18.Pin2 → USB_DP_INT → U6.Pin1(IO1_1) + U6.Pin6(IO1_2) → U1.Pin14(IO20)
  J2.Pin7(DN1) + J2.Pin5(DN2) → USB_DN → R19.Pin1 → R19.Pin2 → USB_DN_INT → U6.Pin3(IO2_1) + U6.Pin4(IO2_2) → U1.Pin13(IO19)
  J2.Pin4(CC1) → R8.Pin1 → R8.Pin2 → GND
  J2.Pin10(CC2) → R9.Pin1 → R9.Pin2 → GND
  J2.Pin1(GND1) + J2.Pin12(GND2) + J2.Pin13(SHELL1) + J2.Pin14(SHELL2) → GND
  J2.Pin3(SBU2) + J2.Pin9(SBU1) → NC (未使用，可悬空)
  U6.Pin5(VBUS) → 5V_PROT
  U6.Pin2(GND) → GND
    │
   GND
```

### 1.2 TP4056 充电管理 + LED指示

```
                     TP4056 (U4)  SOIC-8
                ┌──────────────────────────┐
                │                          │
  GND ───────────┤ Pin1(TEMP)  Pin8(CE) ├──── 5V_PROT
                │ ★TEMP接GND禁用!    │     (接VCC会阻止充电)
                │                          │
  R10(2KΩ)─┬───┤ Pin2(PROG)  Pin7(CHRG)├──── CHRG_STATUS
  R10另一端─┤   │                          │
  GND ──────┘   │ Pin3(GND)  Pin6(STDBY)├─── STDBY_STATUS
                │  │                       │
  5V_PROT ──────┤ Pin4(VCC)  Pin5(BAT) ├──── VBAT
                │                          │
                └──────────────────────────┘
                   │                   │
                  GND                  │
                              ┌───────┤
                              │       │
                              │  ┌────┴────┐
                              │  │ C_BAT   │
                              │  │ 10uF    │
                              │  │Pin1──┤├Pin2│
                              │  │  GND    │
                              │  └─────────┘
                              │
                              VBAT
                              
连接关系:
  5V → F1.Pin1 → F1.Pin2 → 5V_PROT → U4.Pin4(VCC)
  U4.Pin5(BAT) → VBAT → BT1.Pin1(+)
  U4.Pin1(TEMP) → GND
  U4.Pin2(PROG) → R10.Pin1 → R10.Pin2 → GND
  U4.Pin3(GND) → GND
  U4.Pin6(STDBY) → STDBY_STATUS → D5.Pin2(K)
  U4.Pin7(CHRG) → CHRG_STATUS → D4.Pin2(K)
  U4.Pin8(CE) → 5V_PROT
  C_BAT.Pin1 → VBAT, C_BAT.Pin2 → GND

充电红色LED:                       充满绿色LED:
  5V_PROT                           5V_PROT
    │                                 │
  ┌─┴──────┐                        ┌─┴──────┐
  │Pin1 R11 Pin2│                    │Pin1 R12 Pin2│
  │ 1KΩ    │                        │ 1KΩ    │
  └────┬───┘                        └────┬───┘
       │                                 │
    ┌──┴──┐                           ┌──┴──┐
    │Pin1 D4│ (红)                    │Pin1 D5│ (绿)
    │  LED│                           │  LED│
    │Pin2│                           │Pin2│
    └──┬──┘                           └──┬──┘
       │                                 │
  CHRG_STATUS ── U4.Pin7(CHRG)    STDBY_STATUS ── U4.Pin6(STDBY)
  (充电时LOW→LED亮)                  (充满时LOW→LED亮)
  
连接关系:
  5V_PROT → R11.Pin1 → R11.Pin2 → D4.Pin1(A) → D4.Pin2(K) → U4.Pin7(CHRG)
  5V_PROT → R12.Pin1 → R12.Pin2 → D5.Pin1(A) → D5.Pin2(K) → U4.Pin6(STDBY)
```

### 1.3 电池 + 电源开关 + LDO

```
  锂电池 603040 (BT1)                 电源开关 (SW1) MSK-12C02
  ┌──────────────────┐             ┌────────────────────┐
  │  3.7V / 800mAh   │             │                    │
  │                  │     VBAT    │ Pin1(COM) ── VBAT  │
  │ Pin1(+) ─────────┼─────────────┤                    │
  │                  │             │ Pin2(NO) ── VBAT_SW│
  │ Pin2(-) ── GND   │             │                    │
  └──────────────────┘             │ Pin3(NC) ── NC(悬空)│
                                   └────────────────────┘
                                             │
                                          VBAT_SW
                                             │
               ┌───────────┐      ┌──────────┴───────────┐
               │ C14 10uF  │      │                      │
               │Pin1──┤├Pin2│     │  ME6211 (U5) SOT-23  │
               │VBAT_SW GND│     │                      │
               └───────────┘      │ Pin1(VIN) ── VBAT_SW │
                                  │                      │
                                  │ Pin2(VOUT)── 3V3     │ ★Pin2是VOUT!
                                  │                      │
                                  │ Pin3(VSS) ── GND     │ ★Pin3是GND!
               ┌───────────┐      └──────────────────────┘
               │ C9 10uF   │                │
               │Pin1──┤├Pin2│             3V3
               │3V3    GND │
               └───────────┘
               
连接关系:
  BT1.Pin1(+) → SW1.Pin1(COM) → SW1.Pin2(NO) → VBAT_SW → U5.Pin1(VIN)
  U5.Pin2(VOUT) → 3V3
  U5.Pin3(VSS) → GND
  C14.Pin1 → VBAT_SW, C14.Pin2 → GND
  C9.Pin1 → 3V3, C9.Pin2 → GND
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
     │  4(IO4) ─── I2C_SDA ──→ U2.Pin24(SDA)            │
     │  5(IO5) ─── I2C_SCL ──→ U2.Pin23(SCL)            │
     │  6(IO6) ─── MPU6050_INT ←─ U2.Pin12(INT)         │
     │                                                     │
     │  7(IO7) ─── I2S_SCK_MCU ──[R15 33Ω]──→ MIC1.Pin3(SCK)
     │  8(IO15)─── I2S_SD ←──────────────── MIC1.Pin4(SD)
     │  9(IO16)─── I2S_WS_MCU ──[R16 33Ω]──→ MIC1.Pin5(WS)
     │                                                     │
     │ 17(IO9) ─── SPI_SCK_MCU ─[R13 33Ω]─→ LCD1.Pin3(SCL) + J1.Pin5(SCK)
     │ 21(IO13)─── SPI_MOSI_MCU ─[R14 33Ω]─→ LCD1.Pin4(SDA) + J1.Pin7(MOSI)
     │ 20(IO12)─── SPI_MISO ←───────────── J1.Pin8(MISO)  │
     │ 19(IO11)─── LCD_DC ──→ LCD1.Pin6(DC)               │
     │ 22(IO14)─── SPI_CS_LCD ──→ LCD1.Pin7(CS)           │
     │ 18(IO10)─── SPI_CS_SD ──→ J1.Pin2(CS)              │
     │ 10(IO17)─── LCD_RST ──→ LCD1.Pin5(RES)             │
     │                                                     │
     │ 24(IO47)─── UART_TX ──[R20 1KΩ]──→ U3.Pin2(RX)
     │ 25(IO48)─── UART_RX ←──────────── U3.Pin3(TX)
     │ 26(IO45)─── DFPLAYER_BUSY ←─────── U3.Pin16(BUSY)
     │                                                     │
     │ 13(IO19)─── USB_DN_INT ←── USBLC6 ←── Type-C D-   │
     │ 14(IO20)─── USB_DP_INT ←── USBLC6 ←── Type-C D+   │
     │                                                     │
     │ 23(IO21)─── LED_DATA_MCU ──[R17 100Ω]──→ U7.Pin2(1A)
     │                                                     │
     │ 12(IO8) ─── KEY_MODE ──→ SW2.Pin1                  │
     │ 15(IO3) ─── KEY_SELECT ──→ SW3.Pin1                │
     │ 27(IO0) ─── KEY_PLAY ──→ SW4.Pin1                  │
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
        │Pin1 R2 Pin2│            │Pin1 R3 Pin2│
        │  4.7KΩ    │             │  4.7KΩ     │
        └─────┬─────┘             └──────┬─────┘
              │ I2C_SDA                  │ I2C_SCL
              │                          │
         MPU6050 (U2) QFN-24             │
     ┌────────┼──────────────────────────┼──────────────┐
     │        │                          │              │
     │ Pin13(VDD) ── 3V3                                 │
     │                                                  │
     │ Pin8(VLOGIC) ── 3V3                              │
     │                                                  │
     │ Pin18(GND) ── GND                                │
     │                                                  │
     │ Pin24(SDA) ── I2C_SDA ────────────→ U1.Pin4(IO4) │
     │                                                  │
     │ Pin23(SCL) ── I2C_SCL ────────────→ U1.Pin5(IO5) │
     │                                                  │
     │ Pin9(AD0) ── GND  (I2C地址=0x68)                 │
     │                                                  │
     │ Pin12(INT) ── MPU6050_INT ────────→ U1.Pin6(IO6) │
     │                                                  │
     │ Pin1(CLKIN)── GND  ★必须接地                     │
     │                                                  │
     │ Pin11(FSYNC)── GND  ★必须接地                   │
     │                                                  │
     │ Pin20(CPOUT)── C_CP(2.2nF) ── GND ★电荷泵必须   │
     │                                                  │
     │ Pin10(REGOUT)── C_REG(100nF)── GND ★稳压器必须  │
     │                                                  │
     │ Pin19(RESV) ── NC (保留不接)                      │
     │ Pin6(AUX_DA)── NC                                │
     │ Pin7(AUX_CL)── NC                                │
     │ Pin2,3,4,5,14,15,16,17,21,22 ── NC              │
     └──────────────────────────────────────────────────┘

     ┌───────────┐    ┌───────────┐    ┌───────────┐
     │ C4 100nF  │    │C_CP 2.2nF │    │C_REG 100nF│
     │Pin1──┤├Pin2│   │Pin1──┤├Pin2│   │Pin1──┤├Pin2│
     │VDD   GND │    │CPOUT GND │    │REGOUT GND│
     └───────────┘    └───────────┘    └───────────┘
     
连接关系:
  3V3 → U2.Pin13(VDD) + U2.Pin8(VLOGIC)
  U2.Pin24(SDA) → R2.Pin1 → R2.Pin2 → 3V3 (上拉)
  U2.Pin24(SDA) → U1.Pin4(IO4)
  U2.Pin23(SCL) → R3.Pin1 → R3.Pin2 → 3V3 (上拉)
  U2.Pin23(SCL) → U1.Pin5(IO5)
  U2.Pin12(INT) → U1.Pin6(IO6)
  U2.Pin9(AD0) → GND
  U2.Pin1(CLKIN) → GND
  U2.Pin11(FSYNC) → GND
  U2.Pin20(CPOUT) → C_CP.Pin1 → C_CP.Pin2 → GND
  U2.Pin10(REGOUT) → C_REG.Pin1 → C_REG.Pin2 → GND
  U2.Pin18(GND) → GND
  C4.Pin1 → 3V3, C4.Pin2 → GND
```

---

## 四、SPI总线子系统 (LCD + SD卡)

```
  ESP32                  33Ω阻尼              HS20S010B LCD (LCD1)
 ┌──────┐             ┌─────────┐           ┌─────────────────────┐
 │Pin17 │ SPI_SCK_MCU │Pin1 R13 Pin2│ SPI_SCK │                     │
 │(IO9) ├─────────────┤  33Ω   ├───────┬───┤ Pin3(SCL) ── SPI_SCK │
 │      │             └─────────┘       │   │                     │
 │Pin21 │ SPI_MOSI_MCU┌─────────┐      │   │ Pin4(SDA) ── SPI_MOSI│
 │(IO13)├─────────────┤Pin1 R14 Pin2├───┬───┼───┤                     │
 │      │             │  33Ω   │   │   │   │ Pin5(RES) ── LCD_RST │
 │      │             └─────────┘   │   │   │   │                 │
 │Pin20 │ SPI_MISO         │       │   │   │ Pin6(DC) ── LCD_DC  │
 │(IO12)├──────────┐       │       │   │   │   │                 │
 │      │          │       │       │   │   │ Pin7(CS) ── SPI_CS_LCD│
 │Pin19 │ LCD_DC   │       │       │   │   │   │                 │
 │(IO11)├──────────┼───────┼───────┼───┼───┤ Pin8(BLK) ── 3V3    │
 │      │          │       │       │   │   │                     │
 │Pin22 │SPI_CS_LCD│       │       │   │   │ Pin2(VCC) ── 3V3    │
 │(IO14)├──────────┼───────┼───────┼───┼───┤ Pin1(GND) ── GND    │
 │      │          │       │       │   │   │                     │
 │Pin10 │ LCD_RST  │       │       │   │   │ Pin9(FSO) ── NC     │
 │(IO17)├──────────┼───────┼───────┼───┼───┤Pin10(FCS) ── NC     │
 │      │          │       │       │   │   └─────────────────────┘
 │Pin18 │SPI_CS_SD │       │       │   │
 │(IO10)├──────┐   │       │       │   │  去耦: C5(100nF)+C6(10uF)
 │      │      │   │       │       │   │  Pin1 3V3──┤├──Pin2 GND
 └──────┘      │   │       │       │   │
               │   │       │       │   │
               │   │  MicroSD卡座 (J1) │
               │   │  Hirose DM3AT     │
               │   │ ┌─────────────────┤──────┐
               │   │ │                 │      │
               │   └─┤ Pin8(MISO)── SPI_MISO│
               │     │                        │
               │     │ Pin5(SCK) ── SPI_SCK ─┘ (共享)
               │     │                        │
               └─────┤ Pin2(CS) ── SPI_CS_SD│
                     │                        │
                     │ Pin7(MOSI)── SPI_MOSI ─┘ (共享)
                     │                        │
                     │ Pin4(VCC) ── 3V3       │
                     │ Pin3(GND) ── GND      │
                     │ Pin1(SHLD)── GND      │
                     │ Pin9(CD) ── NC        │
                     └────────────────────────┘
                     
连接关系:
  U1.Pin17(IO9) → R13.Pin1 → R13.Pin2 → LCD1.Pin3(SCL) + J1.Pin5(SCK)
  U1.Pin21(IO13) → R14.Pin1 → R14.Pin2 → LCD1.Pin4(SDA) + J1.Pin7(MOSI)
  J1.Pin8(MISO) → U1.Pin20(IO12)
  U1.Pin19(IO11) → LCD1.Pin6(DC)
  U1.Pin22(IO14) → LCD1.Pin7(CS)
  U1.Pin18(IO10) → J1.Pin2(CS)
  U1.Pin10(IO17) → LCD1.Pin5(RES)
```

---

## 五、DFPlayer音频子系统原理图

```
   ESP32                              DFPlayer Mini (U3)
  ┌──────┐                         ┌──────────────────────────┐
  │Pin24 │  UART_TX   ┌────────┐  │                          │
  │(IO47)├────────────┤Pin1 R20 Pin2├──┤ Pin2(RX) ← UART_TX_PROT│
  │      │            │  1KΩ   │  │                          │
  │Pin25 │  UART_RX   └────────┘  │ Pin3(TX) ── UART_RX      │
  │(IO48)├────────────────────────┤                          │
  │      │                        │Pin16(BUSY)── DFPLAYER_BUSY│
  │Pin26 │  DFPLAYER_BUSY         │                          │
  │(IO45)├────────────────────────┤ Pin1(VCC) ── 3V3          │
  └──────┘                        │ Pin7(GND) ── GND          │
                                  │                          │
                                  │ Pin8(SPK1)──┐             │
                                  │            │  扬声器 (LS1)│
                                  │ Pin9(SPK2)──┤  8Ω 0.5W   │
                                  │            │             │
                                  └────────────┼─────────────┘
                                               │
                                  ┌────────────┼──────────┐
                                  │ C7 10uF    │C8 100nF  │
                                  │Pin1 3V3┤├Pin2 GND    │Pin1 3V3┤├Pin2 GND
                                  └────────────┴──────────┘
                                  
连接关系:
  U1.Pin24(IO47) → R20.Pin1 → R20.Pin2 → U3.Pin2(RX)
  U3.Pin3(TX) → U1.Pin25(IO48)
  U3.Pin16(BUSY) → U1.Pin26(IO45)
  U3.Pin1(VCC) → 3V3
  U3.Pin7(GND) → GND
  U3.Pin8(SPK1) → LS1.Pin1(+)
  U3.Pin9(SPK2) → LS1.Pin2(-)
  C7.Pin1 → 3V3, C7.Pin2 → GND
  C8.Pin1 → 3V3, C8.Pin2 → GND
```

---

## 六、INMP441 麦克风子系统原理图

```
  ESP32                          INMP441 (MIC1)
 ┌──────┐                     ┌──────────────────┐
 │Pin7  │ I2S_SCK_MCU         │                  │
 │(IO7) ├──────┐              │ Pin1(VDD)── 3V3  │
 │      │  ┌───┴───────┐     │                  │
 │      │  │Pin1 R15 Pin2│     │ Pin2(GND)── GND  │
 │      │  │  33Ω      │     │                  │
 │      │  └───────┬───┘     │ Pin3(SCK)── I2S_SCK│
 │      │    I2S_SCK──────────┤                  │
 │Pin8  │                     │ Pin4(SD) ── I2S_SD│
 │(IO15)├─── I2S_SD ──────────┤                  │
 │      │                     │ Pin5(WS) ── I2S_WS│
 │Pin9  │ I2S_WS_MCU          │                  │
 │(IO16)├──────┐              │ Pin6(L_R)── GND  │
 │      │  ┌───┴───────┐     └──────────────────┘
 │      │  │Pin1 R16 Pin2│
 │      │  │  33Ω      │     去耦: C10(100nF)
 │      │  └───────┬───┘     Pin1 3V3──┤├──Pin2 GND
 │      │    I2S_WS──┘
 └──────┘
 
连接关系:
  U1.Pin7(IO7) → R15.Pin1 → R15.Pin2 → MIC1.Pin3(SCK)
  MIC1.Pin4(SD) → U1.Pin8(IO15)
  U1.Pin9(IO16) → R16.Pin1 → R16.Pin2 → MIC1.Pin5(WS)
  MIC1.Pin1(VDD) → 3V3
  MIC1.Pin2(GND) → GND
  MIC1.Pin6(L_R) → GND
  C10.Pin1 → 3V3, C10.Pin2 → GND
```

---

## 七、WS2812B LED + 电平转换子系统原理图

```
  ESP32          100Ω串联           SN74AHCT125 (U7) SOIC-14
 ┌──────┐     ┌──────────┐     ┌───────────────────────────────────┐
 │Pin23 │     │Pin1 R17 Pin2│   │                                   │
 │(IO21)├─────┤  100Ω    ├─────┤ Pin2(1A) ← LED_DATA_BUF (3.3V)  │
 │      │     └──────────┘     │                                   │
 └──────┘   LED_DATA_MCU       │ Pin3(1Y) → LED_DATA_5V (5V) ──┐ │
                               │                               │ │
                               │ Pin1(1OE) ── GND (使能)       │ │
                               │ Pin4(2OE) ── GND (使能)       │ │
                               │ Pin5(2A) ── GND               │ │
                               │ Pin9(3OE) ── 5V_PROT (禁用)    │ │
                               │ Pin8(3A) ── GND               │ │
                               │Pin12(4OE) ── 5V_PROT (禁用)   │ │
                               │Pin11(4A) ── GND               │ │
                               │                               │ │
                               │Pin14(VCC) ── 5V_PROT          │ │
                               │ Pin7(GND) ── GND              │ │
                               └───────────────────────────────┘ │
                                                                 │
                               C16(100nF): Pin1 5V_PROT──┤├──Pin2 GND│
                                                                 │
                                          LED_DATA_5V ────────────┘
                                                │
             ┌──────────────────────────────────┘
             │
             ▼ DIN
   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │  D1 WS2812B  │      │  D2 WS2812B  │      │  D3 WS2812B  │
   │              │      │              │      │              │
   │Pin1(VDD)─5V_PROT│   │Pin1(VDD)─5V_PROT│   │Pin1(VDD)─5V_PROT│
   │Pin3(GND)─GND│      │Pin3(GND)─GND│      │Pin3(GND)─GND│
   │Pin4(DIN)←──────│    │Pin4(DIN)←──────│    │Pin4(DIN)←──────│
   │Pin2(DOUT)──────→│   │Pin2(DOUT)──────→│   │Pin2(DOUT)── NC │
   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
          │                     │                     │
   C11(100nF)             C12(100nF)            C13(100nF)
   Pin1 5V_PROT┤├Pin2 GND  Pin1 5V_PROT┤├Pin2 GND  Pin1 5V_PROT┤├Pin2 GND
   
连接关系:
  U1.Pin23(IO21) → R17.Pin1 → R17.Pin2 → U7.Pin2(1A) → U7.Pin3(1Y) → D1.Pin4(DIN)
  D1.Pin2(DOUT) → D2.Pin4(DIN) → D2.Pin2(DOUT) → D3.Pin4(DIN)
  D1/D2/D3.Pin1(VDD) → 5V_PROT
  D1/D2/D3.Pin3(GND) → GND
```

---

## 八、按键子系统原理图 (×3组相同结构)

```
按键1 (模式选择):                按键2 (手势选择):                按键3 (播放/确认):

        3V3                            3V3                            3V3
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │Pin1 R4 Pin2│                  │Pin1 R5 Pin2│                  │Pin1 R6 Pin2│
   │  10KΩ     │                  │  10KΩ     │                  │  10KΩ     │
   └─────┬─────┘                  └─────┬─────┘                  └─────┬─────┘
         │ KEY_MODE                     │ KEY_SELECT                   │ KEY_PLAY
         ├───── U1.Pin12(IO8)          ├──── U1.Pin15(IO3)          ├──── U1.Pin27(IO0)
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │Pin1 C18 Pin2│                 │Pin1 C19 Pin2│                 │Pin1 C20 Pin2│
   │ 100nF  GND│                  │ 100nF  GND│                  │ 100nF  GND│
   └───────────┘                  └───────────┘                  └───────────┘
         │                              │                              │
   ┌─────┴─────┐                  ┌─────┴─────┐                  ┌─────┴─────┐
   │Pin1 SW2 Pin2│                 │Pin1 SW3 Pin2│                 │Pin1 SW4 Pin2│
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
| IO19 | 13 | USB_DN_INT | R19(22Ω)+U6(ESD) | J2(USB).Pin7(DN1),Pin5(DN2) |
| IO20 | 14 | USB_DP_INT | R18(22Ω)+U6(ESD) | J2(USB).Pin6(DP1),Pin8(DP2) |
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
| 5V | J2.Pin2(VBUS1), J2.Pin11(VBUS2) | F1.Pin1 |
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
| USB_DP | J2.Pin6(DP1), J2.Pin8(DP2) | R18.Pin1 | - |
| USB_DP_INT | R18.Pin2 | U6.Pin1(IO1_1), U6.Pin6(IO1_2), U1.Pin14(IO20) | - |
| USB_DN | J2.Pin7(DN1), J2.Pin5(DN2) | R19.Pin1 | - |
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
| (CC1) | J2.Pin5(CC1) | R8.Pin1 | R8.2→GND |
| (CC2) | J2.Pin10(CC2) | R9.Pin1 | R9.2→GND |

---

## 十、元器件封装引脚标号表

> **说明**: 本表列出所有元器件的封装引脚标号，便于PCB布局和原理图绘制时参考。

### 10.1 ESP32-S3-WROOM-1N16R8 (U1)

| 封装Pin | IO名称 | 功能 | 连接 |
|---------|--------|------|------|
| 1 | GND1 | 地 | GND |
| 2 | 3V3 | 电源输入 | 3V3 |
| 3 | EN | 使能 | R1→3V3, C_EN→GND |
| 4 | IO4 | GPIO | I2C_SDA |
| 5 | IO5 | GPIO | I2C_SCL |
| 6 | IO6 | GPIO | MPU6050_INT |
| 7 | IO7 | GPIO | I2S_SCK_MCU |
| 8 | IO15 | GPIO | I2S_SD |
| 9 | IO16 | GPIO | I2S_WS_MCU |
| 10 | IO17 | GPIO | LCD_RST |
| 11 | IO18 | GPIO | NC (USB_D-) |
| 12 | IO8 | GPIO | KEY_MODE |
| 13 | IO19 | GPIO | USB_DN_INT |
| 14 | IO20 | GPIO | USB_DP_INT |
| 15 | IO3 | GPIO | KEY_SELECT |
| 16 | IO46 | GPIO | R7→GND (下拉) |
| 17 | IO9 | GPIO | SPI_SCK_MCU |
| 18 | IO10 | GPIO | SPI_CS_SD |
| 19 | IO11 | GPIO | LCD_DC |
| 20 | IO12 | GPIO | SPI_MISO |
| 21 | IO13 | GPIO | SPI_MOSI_MCU |
| 22 | IO14 | GPIO | SPI_CS_LCD |
| 23 | IO21 | GPIO | LED_DATA_MCU |
| 24 | IO47 | GPIO | UART_TX |
| 25 | IO48 | GPIO | UART_RX |
| 26 | IO45 | GPIO | DFPLAYER_BUSY |
| 27 | IO0 | GPIO | KEY_PLAY |
| 28 | IO35_PSRAM | NC | PSRAM占用 |
| 29 | IO36_PSRAM | NC | PSRAM占用 |
| 30 | IO37_PSRAM | NC | PSRAM占用 |
| 31 | IO38 | GPIO | NC |
| 32 | IO39 | GPIO | NC |
| 33 | IO40 | GPIO | NC |
| 34 | IO41 | GPIO | NC |
| 35 | IO42 | GPIO | NC |
| 36 | RXD0 | GPIO | NC |
| 37 | TXD0 | GPIO | NC |
| 38 | IO2 | GPIO | NC |
| 39 | IO1 | GPIO | NC |
| 40 | GND2 | 地 | GND |
| 41 | EPAD | 地 | GND (散热焊盘) |

**封装**: SMD, 18.0×25.5mm, 41引脚

---

### 10.2 TP4056 充电管理芯片 (U4)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | TEMP | 温度监测 | GND (禁用) |
| 2 | PROG | 充电电流设置 | R10(2KΩ)→GND |
| 3 | GND | 地 | GND |
| 4 | VCC | 输入电源 | 5V_PROT |
| 5 | BAT | 电池连接 | VBAT |
| 6 | STDBY | 充满指示(开漏) | D5 LED (绿) |
| 7 | CHRG | 充电指示(开漏) | D4 LED (红) |
| 8 | CE | 芯片使能 | 5V_PROT |

**封装**: SOIC-8 (SOP-8), 3.9×4.9mm, 引脚间距1.27mm

---

### 10.3 ME6211 LDO稳压器 (U5)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VIN | 输入电压 | VBAT_SW |
| 2 | VOUT | 稳压输出 | 3V3 |
| 3 | VSS | 地 | GND |

**封装**: SOT-23-3, 2.9×1.6mm

---

### 10.4 USBLC6-2SC6 ESD保护芯片 (U6)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | IO1_1 | I/O 1 输入 | USB_DP_INT |
| 2 | GND | 地 | GND |
| 3 | IO2_1 | I/O 2 输入 | USB_DN_INT |
| 4 | IO2_2 | I/O 2 输出 | USB_DN_INT |
| 5 | VBUS | VBUS电源 | 5V_PROT |
| 6 | IO1_2 | I/O 1 输出 | USB_DP_INT |

**封装**: SOT-23-6, 3.0×1.6mm

---

### 10.5 SN74AHCT125 电平转换器 (U7)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1OE | 通道1输出使能(低有效) | GND |
| 2 | 1A | 通道1输入 | LED_DATA_BUF |
| 3 | 1Y | 通道1输出 | LED_DATA_5V |
| 4 | 2OE | 通道2输出使能(低有效) | GND |
| 5 | 2A | 通道2输入 | GND |
| 6 | 2Y | 通道2输出 | NC |
| 7 | GND | 地 | GND |
| 8 | 3A | 通道3输入 | GND |
| 9 | 3OE | 通道3输出使能(低有效) | 5V_PROT (禁用) |
| 10 | 3Y | 通道3输出 | NC |
| 11 | 4A | 通道4输入 | GND |
| 12 | 4OE | 通道4输出使能(低有效) | 5V_PROT (禁用) |
| 13 | 4Y | 通道4输出 | NC |
| 14 | VCC | 电源 | 5V_PROT |

**封装**: SOIC-14, 3.9×8.7mm, 引脚间距1.27mm

---

### 10.6 MPU6050 运动传感器 (U2)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | CLKIN | 外部时钟输入 | GND (不用) |
| 2-5 | NC | 未内部连接 | NC |
| 6 | AUX_DA | 辅助I2C数据 | NC |
| 7 | AUX_CL | 辅助I2C时钟 | NC |
| 8 | VLOGIC | 数字I/O参考电压 | 3V3 |
| 9 | AD0 | I2C地址LSB | GND (地址=0x68) |
| 10 | REGOUT | 内部稳压输出 | C_REG(100nF)→GND |
| 11 | FSYNC | 帧同步输入 | GND (不用) |
| 12 | INT | 中断输出 | MPU6050_INT |
| 13 | VDD | 主电源 | 3V3 |
| 14-17 | NC | 未内部连接 | NC |
| 18 | GND | 地 | GND |
| 19 | RESV | 保留 | NC |
| 20 | CPOUT | 电荷泵输出 | C_CP(2.2nF)→GND |
| 21-22 | NC | 未内部连接 | NC |
| 23 | SCL | I2C时钟 | I2C_SCL |
| 24 | SDA | I2C数据 | I2C_SDA |
| EP | GND | 散热焊盘 | GND |

**封装**: QFN-24, 4×4mm, 引脚间距0.5mm

---

### 10.7 HS20S010B LCD模块 (LCD1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | GND | 地 | GND |
| 2 | VCC | 电源 | 3V3 |
| 3 | SCL | SPI时钟 | SPI_SCK |
| 4 | SDA | SPI数据 | SPI_MOSI |
| 5 | RES | 复位(低有效) | LCD_RST |
| 6 | DC | 数据/命令选择 | LCD_DC |
| 7 | CS | 片选(低有效) | SPI_CS_LCD |
| 8 | BLK | 背光控制 | 3V3 |
| 9 | FSO | 字库数据输出 | NC |
| 10 | FCS | 字库IC片选 | NC |

**封装**: 10引脚排针, 2.54mm间距

---

### 10.8 MicroSD卡座 (J1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | SHIELD | 屏蔽 | GND |
| 2 | CS | 片选 | SPI_CS_SD |
| 3 | GND | 地 | GND |
| 4 | VCC | 电源 | 3V3 |
| 5 | SCK | SPI时钟 | SPI_SCK |
| 6 | NC | 未使用 | NC |
| 7 | MOSI | SPI主出从入 | SPI_MOSI |
| 8 | MISO | SPI主入从出 | SPI_MISO |
| 9 | CD | 卡检测 | NC |

**封装**: Hirose DM3AT-SF-PEJM5

---

### 10.9 DFPlayer Mini 音频模块 (U3)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VCC | 电源 | 3V3 |
| 2 | RX | UART接收 | UART_TX_PROT |
| 3 | TX | UART发送 | UART_RX |
| 4 | DAC_R | DAC右声道 | NC |
| 5 | DAC_L | DAC左声道 | NC |
| 6 | NC | 未使用 | NC |
| 7 | GND | 地 | GND |
| 8 | SPK1 | 扬声器1 | SPEAKER+ |
| 9 | SPK2 | 扬声器2 | SPEAKER- |
| 10 | NC | 未使用 | NC |
| 11 | IO1 | GPIO1 | NC |
| 12 | IO2 | GPIO2 | NC |
| 13 | ADKEY1 | 按键1 | NC |
| 14 | ADKEY2 | 按键2 | NC |
| 15 | USB_P | USB+ | NC |
| 16 | BUSY | 播放状态 | DFPLAYER_BUSY |

**封装**: 16引脚排针, 2.54mm间距

---

### 10.10 INMP441 MEMS麦克风 (MIC1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VDD | 电源 | 3V3 |
| 2 | GND | 地 | GND |
| 3 | SCK | I2S时钟 | I2S_SCK |
| 4 | SD | I2S数据 | I2S_SD |
| 5 | WS | I2S字选择 | I2S_WS |
| 6 | L_R | 声道选择 | GND |

**封装**: 6引脚排针, 2.54mm间距

---

### 10.11 WS2812B RGB LED (D1/D2/D3)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VDD | 电源 | 5V_PROT |
| 2 | DOUT | 数据输出 | 下一级DIN (D1→D2→D3) |
| 3 | GND | 地 | GND |
| 4 | DIN | 数据输入 | LED_DATA_5V (D1) / 上一级DOUT |

**封装**: PLCC-4, 5.0×5.0mm, 引脚间距3.2mm

---

### 10.12 USB Type-C 母座 (J2)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | GND1 | 地 | GND |
| 2 | VBUS1 | VBUS电源 | 5V |
| 3 | SBU2 | 辅助信号2 | NC (未使用) |
| 4 | CC1 | 配置通道1 | R8(5.1KΩ)→GND |
| 5 | DN2 | USB数据- (B侧) | USB_DN |
| 6 | DP1 | USB数据+ (A侧) | USB_DP |
| 7 | DN1 | USB数据- (A侧) | USB_DN |
| 8 | DP2 | USB数据+ (B侧) | USB_DP |
| 9 | SBU1 | 辅助信号1 | NC (未使用) |
| 10 | CC2 | 配置通道2 | R9(5.1KΩ)→GND |
| 11 | VBUS2 | VBUS电源 | 5V |
| 12 | GND2 | 地 | GND |
| 13 | SHELL1 | 金属外壳 | GND |
| 14 | SHELL2 | 金属外壳 | GND |

**封装**: TYPE-C 16PIN 2MD(073), 14引脚 SMD（左侧12引脚 + 右侧2个SHELL引脚）
**制造商**: 深圳市首韩科技有限公司 (SHOU HAN)
**规格**: USB 2.0, 最大3A电流, 工作温度-25°C~+85°C
**引脚排列**: 左侧从上到下Pin1-12, 右侧从上到下Pin13-14(SHELL)

---

### 10.13 PTC自恢复保险丝 (F1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 输入端 | 5V |
| 2 | 2 | 输出端 | 5V_PROT |

**封装**: SMD 1206, 3.2×1.6mm

**规格**: 750mA保持电流, 1.5A触发电流, 13.2V最大电压

---

### 10.14 LED指示灯 (D4/D5)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | A | 阳极 | R11/R12(1KΩ)→5V_PROT |
| 2 | K | 阴极 | CHRG_STATUS/STDBY_STATUS |

**封装**: SMD 0805, 2.0×1.2mm

**颜色**: D4=红色(充电), D5=绿色(充满)

---

### 10.15 电源开关 (SW1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | COM | 公共端 | VBAT |
| 2 | NO | 常开端 | VBAT_SW |
| 3 | NC | 常闭端 | NC (悬空) |

**封装**: MSK-12C02, SMD滑动开关

**规格**: SPDT, 0.3A, 6V DC

---

### 10.16 按键开关 (SW2/SW3/SW4)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 按键端1 | KEY_MODE/SELECT/PLAY |
| 2 | 2 | 按键端2 | GND |

**封装**: SMD按键开关, 2引脚

---

### 10.17 电阻 (R1-R20)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 引脚1 | 网络1 |
| 2 | 2 | 引脚2 | 网络2 |

**封装**: SMD 0805, 2.0×1.2mm

**阻值**:
- R1: 10KΩ (EN上拉)
- R2/R3: 4.7KΩ (I2C上拉)
- R4/R5/R6: 10KΩ (按键上拉)
- R7: 10KΩ (IO46下拉)
- R8/R9: 5.1KΩ (USB CC下拉)
- R10: 2KΩ (TP4056 PROG)
- R11/R12: 1KΩ (LED限流)
- R13/R14/R15/R16: 33Ω (SPI/I2S阻尼)
- R17: 100Ω (LED数据串联)
- R18/R19: 22Ω (USB数据串联)
- R20: 1KΩ (DFPlayer RX保护)

---

### 10.18 电容 (C1-C20, C_EN, C_BAT, C_CP, C_REG)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 正极 | 网络1 |
| 2 | 2 | 负极 | GND |

**封装**: 
- 100nF: SMD 0805, 2.0×1.2mm
- 1uF: SMD 0805, 2.0×1.2mm
- 2.2nF: SMD 0603, 1.6×0.8mm
- 10uF: SMD 0805, 2.0×1.2mm
- 22uF: SMD 0805, 2.0×1.2mm

**容值**:
- C1/C2/C4/C5/C7/C8/C9/C10/C11/C12/C13/C16: 100nF (去耦)
- C3/C6/C14/C15/C17: 10uF (滤波)
- C_BAT: 10uF (TP4056 BAT去耦)
- C_EN: 1uF (ESP32 EN复位延迟)
- C_CP: 2.2nF (MPU6050电荷泵)
- C_REG: 100nF (MPU6050稳压器)
- C18/C19/C20: 100nF (按键去抖)
- C17: 22uF (VBUS大容量滤波)

---

### 10.19 电池 (BT1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | + | 正极 | VBAT |
| 2 | - | 负极 | GND |

**规格**: 603040, 3.7V, 800mAh, 锂电池

---

### 10.20 扬声器 (LS1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | + | 正极 | DFPlayer SPK1 |
| 2 | - | 负极 | DFPlayer SPK2 |

**规格**: 8Ω, 0.5W

---

*v2.3 所有引脚编号严格按各芯片数据手册。可作为KiCad绘制原理图和PCB布局的完整参考。*
