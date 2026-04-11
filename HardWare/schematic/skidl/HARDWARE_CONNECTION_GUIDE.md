# CyberWand v2.4 - 完整电路原理图连接指南

> **版本**: v2.4 | **日期**: 2026-02
> **网表**: `output/cyberwand_netlist.net`
> **变更**: 去掉 DFPlayer 音频模块；串口调试复用 USB（Type-C 直连电脑，无需外接 USB 转 TTL）。
> **总元件/网络**: 见网表
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
                     TP4056 (U4)  SOIC-8 (9脚含EP)
                ┌──────────────────────────┐
                │  Pin9(EP) 散热焊盘 → GND  │  ※ 原理图符号第9脚EP需接GND
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
  U4.Pin9(EP) → GND   （散热焊盘，必须接GND以散热并稳定地参考）
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

**说明**：开关采用 MSK12C02 四脚 SP3T（单刀三掷），公共端为 **Pin4**；LDO 采用 ME6211C33M5G-N **五脚** 封装（含 CE、NC）。若原理图符号内开关带 GND 标识，多为符号库的机械地或误绘，**切勿将开关公共端(Pin4)接 GND**，否则会短路电池。

```
  锂电池 603040 (BT1)                 电源开关 (SW1) MSK12C02 四脚 SP3T
  ┌──────────────────┐             ┌────────────────────────────┐
  │  3.7V / 800mAh   │             │  Pin4(COM) ← 公共端        │
  │                  │     VBAT    │  Pin1/Pin3 → NC(悬空, OFF) │
  │ Pin1(+) ─────────┼─────────────┤  Pin2 → VBAT_SW (ON 位)   │
  │                  │             │  ※ COM 接电池正，勿接 GND   │
  │ Pin2(-) ── GND   │             └────────────────────────────┘
  └──────────────────┘                          │
                                                 VBAT_SW
                                                 │
               ┌───────────┐      ┌──────────────┴────────────────┐
               │ C14 10uF  │      │  ME6211C33M5G-N (U5) 五脚 LDO  │
               │Pin1──┤├Pin2│     │                                │
               │VBAT_SW GND│      │  Pin1(VIN)  ← VBAT_SW          │
               └───────────┘      │  Pin2(VSS)  ← GND             │
                                  │  Pin3(CE)   ← VBAT_SW (使能)  │
                                  │  Pin4(NC)   ← 悬空             │
                                  │  Pin5(VOUT) → 3V3             │
               ┌───────────┐      └────────────────────────────────┘
               │ C9 10uF   │                │
               │Pin1──┤├Pin2│             3V3
               │3V3    GND │
               └───────────┘
               
连接关系:
  BT1.Pin1(+) → SW1.Pin4(COM) → SW1.Pin2 → VBAT_SW   （Pin2 为“开”位；Pin1/Pin3 悬空为“关”）
  VBAT_SW → U5.Pin1(VIN), U5.Pin3(CE)   （CE 接 VBAT_SW，开关打开时 LDO 使能）
  U5.Pin2(VSS) → GND
  U5.Pin4(NC) → 悬空
  U5.Pin5(VOUT) → 3V3
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
     │  7(IO7) ─── NC (预留)              │
     │  8(IO15)─── NC (预留)              │
     │  9(IO16)─── NC (预留)              │
     │                                                     │
     │ 17(IO9) ─── SPI_SCK_MCU ─[R13 33Ω]─→ LCD1.Pin3(CLK) + J1.Pin5(CLK)
     │ 21(IO13)─── SPI_MOSI_MCU ─[R14 33Ω]─→ LCD1.Pin4(SDA) + J1.Pin8(DAT1/MOSI)
     │ 20(IO12)─── SPI_MISO ←───────────── J1.Pin7(DAT0/MISO)
     │ 19(IO11)─── LCD_DC ──→ LCD1.Pin6(DC)               │
     │ 22(IO14)─── SPI_CS_LCD ──→ LCD1.Pin7(CS)           │
     │ 18(IO10)─── SPI_CS_SD ──→ J1.Pin3(CMD)              │
     │ 10(IO17)─── LCD_RST ──→ LCD1.Pin5(RES)             │
     │                                                     │
     │ 24(IO47)─── NC (预留)              │
     │ 25(IO48)─── NC (预留)              │
     │ 26(IO45)─── NC (预留)              │
     │                                                     │
     │ 13(IO19)─── USB_DN_INT  ←── 串口调试复用 USB (D-) ←── USBLC6 ←── Type-C D-   │
     │ 14(IO20)─── USB_DP_INT ←── 串口调试复用 USB (D+)   │
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
     │ Pin8(VLOGIC)── C_VLOGIC(100nF)── GND ★去耦推荐  │
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

**SPI 阻尼电阻说明**：SCK、MOSI 由 MCU 驱动，串联 33Ω（R13/R14）用于阻抗匹配与反射阻尼。**MISO** 由从设备（SD 卡）驱动、MCU 仅接收，本图采用**直连**（不加电阻）；若希望与 SCK/MOSI 一致可选用 33Ω 串联，取舍见文档内“不加/加电阻”对比说明。

```
  ESP32                  33Ω阻尼              HS20S010B LCD (LCD1)
 ┌──────┐             ┌─────────┐           ┌─────────────────────┐
 │Pin17 │ SPI_SCK_MCU │Pin1 R13 Pin2│ SPI_SCK │                     │
 │(IO9) ├─────────────┤  33Ω    ├───────┬───┤ Pin3(CLK) ── SPI_SCK │
 │      │             └─────────┘       │   │                     │
 │Pin21 │ SPI_MOSI_MCU┌─────────┐      │   │ Pin4(SDA) ── SPI_MOSI│
 │(IO13)├─────────────┤Pin1 R14 Pin2├───┬───┼───┤                     │
 │      │             │  33Ω   │   │   │   │ Pin5(RES) ── LCD_RST │
 │      │             └─────────┘   │   │   │   │                 │
 │Pin20 │ SPI_MISO         │       │   │   │ Pin6(DC) ── LCD_DC  │
 │(IO12)├──────────┐       │       │   │   │   │                 │
 │      │          │       │       │   │   │ Pin7(CS1)── SPI_CS_LCD│
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
               │   │  MicroSD卡座 (J1) DM3AT-SF-PEJM5  14引脚
               │   │ ┌──────────────────┬──────────────────┐
               │   │ │ 左侧 1-8(上→下)  │ 右侧 14-9(上→下) │
               │   │ │ 1 DAT2    NC      │ 14 (未标)  NC    │
               │   │ │ 2 CD/DAT3 NC      │ 13 (未标)  NC    │
               │   └─┤ 3 CMD   SPI_CS_SD│ 12 (未标)  NC    │
               │     │ 4 VDD   3V3       │ 11 SW_A    NC    │
               │     │ 5 CLK   SPI_SCK   │ 10 (未标)  NC    │
               │     │ 6 VSS   GND       │  9 SW_B    NC    │
               │     │ 7 DAT0  SPI_MISO ─┘                  │
               └─────┤ 8 DAT1  SPI_MOSI ─┘                  │
                     └──────────────────┴──────────────────┘
                     ※ SPI 模式使用 Pin3/4/5/6/7/8，其余 8 脚 NC
                     
连接关系:
  U1.Pin17(IO9) → R13.Pin1 → R13.Pin2 → LCD1.Pin3(CLK) + J1.Pin5(CLK)
  U1.Pin21(IO13) → R14.Pin1 → R14.Pin2 → LCD1.Pin4(SDA) + J1.Pin8(DAT1)
  J1.Pin7(DAT0) → U1.Pin20(IO12)   （MISO 直连，无串联电阻）
  U1.Pin19(IO11) → LCD1.Pin6(DC)
  U1.Pin22(IO14) → LCD1.Pin7(CS1)
  U1.Pin18(IO10) → J1.Pin3(CMD)
  U1.Pin10(IO17) → LCD1.Pin5(RES)
```

### 4.1 LCD1 (HS20S010B) 全20引脚接法

**为什么有 20 个引脚但连接图只画了约 10 个？**  
模块是 **2×10 排针**：上排 Pin1–10 与下排 Pin11–20 **功能重复**（同一组信号引出两次）。例如 Pin1(GND) 与 Pin12(GND_B)、Pin3(CLK) 与 Pin16(CLK_B) 等是同一信号，所以**逻辑上只需约 10 种连接**；连接图通常只画出这 10 组，其余引脚要么与它们同网络，要么 NC。详细说明见 [LCD_20引脚说明.md](LCD_20引脚说明.md)。

| 封装Pin | 名称 | 接法 | 说明 |
|---------|------|------|------|
| 1 | GND | GND | 与 Pin12 同信号 |
| 2 | VCC | 3V3 | 与 Pin11 同信号 |
| 3 | CLK | SPI_SCK | 与 Pin16 同信号 |
| 4 | SDA | SPI_MOSI | 与 Pin17 同信号 |
| 5 | RES | LCD_RST | 与 Pin19 同信号 |
| 6 | DC | LCD_DC | 与 Pin18 同信号 |
| 7 | CS1 | SPI_CS_LCD | 与 Pin20 同信号 |
| 8 | BLK | 3V3 | 背光控制，仅上排 |
| 9 | FS0 | **NC (悬空)** | 字库未用时悬空 |
| 10 | FCS | **NC (悬空)** | 字库未用时悬空 |
| 11 | VCC_B | 3V3 | 建议接 3V3 以改善供电 |
| 12 | GND_B | GND | 建议接 GND |
| 13 | BLA | **NC (悬空)** | 背光阳极，按需接或 NC |
| 14 | FCS_B | **NC (悬空)** | 与 Pin10 同信号，可 NC |
| 15 | FS0_B | **NC (悬空)** | 与 Pin9 同信号，可 NC |
| 16 | CLK_B | **NC (悬空)** | 与 Pin3 同信号，可 NC |
| 17 | SDA_B | **NC (悬空)** | 与 Pin4 同信号，可 NC |
| 18 | DC_B | **NC (悬空)** | 与 Pin6 同信号，可 NC |
| 19 | RES_B | **NC (悬空)** | 与 Pin5 同信号，可 NC |
| 20 | CS1_B | **NC (悬空)** | 与 Pin7 同信号，可 NC |

### 4.2 J1 (MicroSD DM3AT-SF-PEJM5) 全14引脚接法

**为什么 14 个引脚只有 6 个在用？**  
本电路采用 **SPI 模式** 访问 SD 卡。SPI 模式只需：**CMD(片选)、VDD、VSS、CLK、DAT0(MISO)、DAT1(MOSI)** 共 6 个引脚。其余引脚在 SPI 模式下不用：**DAT2、CD/DAT3** 为 SD 模式或卡检测用，**SW_A/SW_B** 为卡座机械开关，**Pin10/12/13/14** 未标注，均作 **NC (悬空)** 即可。

| 封装Pin | 名称 | 接法 | 说明 |
|---------|------|------|------|
| 1 | DAT2 | **NC (悬空)** | SD 4bit 模式用，SPI 不接 |
| 2 | CD/DAT3 | **NC (悬空)** | 卡检测/数据3，SPI 可不接 |
| 3 | CMD | SPI_CS_SD | SPI 片选 |
| 4 | VDD | 3V3 | 电源 |
| 5 | CLK | SPI_SCK | SPI 时钟 |
| 6 | VSS | GND | 地 |
| 7 | DAT0 | SPI_MISO | SPI 主入从出 |
| 8 | DAT1 | SPI_MOSI | SPI 主出从入 |
| 9 | SW_B | **NC (悬空)** | 卡座开关 B |
| 10 | (未标注) | **NC (悬空)** | - |
| 11 | SW_A | **NC (悬空)** | 卡座开关 A |
| 12 | (未标注) | **NC (悬空)** | - |
| 13 | (未标注) | **NC (悬空)** | - |
| 14 | (未标注) | **NC (悬空)** | - |

---

## 五、串口调试与固件烧录（USB 复用，无需独立 UART 模块）

魔杖通过 **同一根 Type-C 线** 连接电脑即可完成 **串口打印调试** 和 **固件烧录/升级**，**无需外接 USB 转 TTL 或独立 UART 排针**。即：**当前项目使用 USB 连接电脑的方式进行开发调试与固件更新（非无线 OTA）**。

- **硬件**：现有 USB Type-C 座 (J2) 的 D+/D- 已接 ESP32-S3 的 **IO20(DP)**、**IO19(DN)**，经 ESD 保护 (U6) 和串联电阻后进 MCU。
- **串口调试**：ESP32-S3 内置 **USB Serial/JTAG**，连接电脑后会枚举为 **USB CDC 串口**；固件中 `Serial` 默认即走该 USB，`Serial.print` 等输出直接在电脑端串口监视器显示。
- **固件烧录/升级**：同一 USB 路径支持 **USB 下载模式**（进入 bootloader 后），可用 Arduino IDE“上传”、`idf.py flash`、esptool 等通过 Type-C 线烧录或升级固件，**即通过 USB 连电脑的方式做“有线 OTA”**。
- **使用**：Type-C 线连接魔杖与电脑 → 电脑识别 COM 口 → 串口监视器查看打印，或运行烧录工具进行固件更新。

```
  J2(Type-C)  ←──USB线──→  电脑
       │
   D+/D- → U6(ESD) → R18/R19(22Ω) → U1.Pin14(IO20)/Pin13(IO19)
                              ↑
                    串口调试与烧录均通过此 USB 路径
```

### 5.1 通过 USB 烧录程序：电路是否支持？需要怎么做？

**结论：当前电路已支持通过 USB 烧录，无需改原理图。**

| 项目 | 说明 |
|------|------|
| **电路是否支持** | ✅ 支持。J2(Type-C) 的 D+/D- 已接 ESP32-S3 的 IO20/IO19，ESP32-S3 内置 **USB Serial/JTAG**，可做 CDC 串口和 **USB 下载（烧录）**。 |
| **是否需要额外设计** | ❌ 不需要。不接 USB 转 TTL、不增加 UART 排针，仅用现有 J2 即可。 |
| **BOOT/下载模式** | IO0 已接 **KEY_PLAY (SW4)**：需要进入下载模式时，可 **按住 PLAY 键** 再上电或复位，再在电脑上执行烧录。部分工具（如 idf.py、Arduino）也会通过 USB 自动尝试进入下载模式。 |

**操作步骤（你需要做的）：**

1. **接线**  
   - 用 **Type-C 数据线** 将魔杖 **J2** 与 **电脑 USB 口** 连接。  
   - 板子可由 USB 供电，或电池+开关供电均可（保证 3.3V 正常即可）。

2. **进入下载模式（若工具未自动进入）**  
   - **按住 KEY_PLAY（SW4）** 不松开 → 再 **上电** 或 **重新插拔 USB**，然后松开按键。  
   - 或：先按住 KEY_PLAY，再短接 EN 与 GND 一下做复位（若板上有预留复位点），再松开 KEY_PLAY。  
   - 使用 Arduino IDE 或 `idf.py flash` 时，多数情况会通过 USB 自动进入下载，无需每次手动按键。

3. **在电脑上烧录**  
   - **Arduino IDE**：选择开发板为 **ESP32-S3**（如 “ESP32S3 Dev Module”），选择对应的 **USB CDC 或 USB JTAG 的 COM 口**，点击“上传”。  
   - **ESP-IDF**：在工程目录执行 `idf.py -p COMx flash`（COMx 为电脑识别的端口号）。  
   - **esptool**：`esptool.py -p COMx write_flash 0x0 firmware.bin`。

4. **驱动**  
   - 若电脑未识别到 COM 口，请安装乐鑫 **CP210x / CH343 或 ESP32-S3 USB JTAG 相关驱动**（视模块与系统而定）。

**硬件要点小结**：  
- **J2** → D+/D- → **U6(ESD)** → **R18/R19(22Ω)** → **U1.IO20 / U1.IO19**：已满足 USB 烧录与串口调试。  
- **IO0** 接 **KEY_PLAY**：必要时可手动进入下载模式，**无需在电路上再做设计**。

---

## 六、WS2812B LED + 电平转换子系统原理图

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
   ┌──────────────┐
   │  D1 WS2812B  │  单颗可编程 RGB LED
   │              │
   │Pin1(VDD)─5V_PROT│
   │Pin3(GND)─GND│
   │Pin4(DIN)←──────│
   │Pin2(DOUT)─ NC  │  (无级联，悬空)
   └──────┬───────┘
          │
   C11(100nF)
   Pin1 5V_PROT┤├Pin2 GND

连接关系:
  U1.Pin23(IO21) → R17.Pin1 → R17.Pin2 → U7.Pin2(1A) → U7.Pin3(1Y) → D1.Pin4(DIN)
  D1.Pin2(DOUT) → NC (悬空)
  D1.Pin1(VDD) → 5V_PROT, D1.Pin3(GND) → GND
```

---

## 七、按键子系统原理图 (×3组相同结构)

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

## 八、完整引脚对引脚连线表

### ESP32-S3 Pin → 目标

| ESP32引脚 | 物理Pin | 网络名 | → 中间元件 | → 目标芯片.引脚 |
|-----------|---------|--------|-----------|----------------|
| IO0 | 27 | KEY_PLAY | R6(10K)→3V3, C20(100nF)→GND | SW4.Pin1 |
| IO3 | 15 | KEY_SELECT | R5(10K)→3V3, C19(100nF)→GND | SW3.Pin1 |
| IO4 | 4 | I2C_SDA | R2(4.7K)→3V3 | U2(MPU6050).Pin24 |
| IO5 | 5 | I2C_SCL | R3(4.7K)→3V3 | U2(MPU6050).Pin23 |
| IO6 | 6 | MPU6050_INT | 直连 | U2(MPU6050).Pin12 |
| IO7 | 7 | NC (预留) | 悬空 | - |
| IO8 | 12 | KEY_MODE | R4(10K)→3V3, C18(100nF)→GND | SW2.Pin1 |
| IO9 | 17 | SPI_SCK_MCU | R13(33Ω) | LCD1.Pin3 + J1.Pin5 |
| IO10 | 18 | SPI_CS_SD | 直连 | J1(SD).Pin3(CMD) |
| IO11 | 19 | LCD_DC | 直连 | LCD1.Pin6 |
| IO12 | 20 | SPI_MISO | 直连 | J1(SD).Pin7(DAT0) |
| IO13 | 21 | SPI_MOSI_MCU | R14(33Ω) | LCD1.Pin4 + J1.Pin8(DAT1) |
| IO14 | 22 | SPI_CS_LCD | 直连 | LCD1.Pin7 |
| IO15 | 8 | NC (预留) | 悬空 | - |
| IO16 | 9 | NC (预留) | 悬空 | - |
| IO17 | 10 | LCD_RST | 直连 | LCD1.Pin5 |
| IO19 | 13 | USB_DN_INT | R19(22Ω)+U6(ESD) | J2(USB).Pin7(DN1),Pin5(DN2) |
| IO20 | 14 | USB_DP_INT | R18(22Ω)+U6(ESD) | J2(USB).Pin6(DP1),Pin8(DP2) |
| IO21 | 23 | LED_DATA_MCU | R17(100Ω)→U7(74AHCT125) | D1(WS2812B).Pin4 |
| IO45 | 26 | NC (预留) | 悬空 | - |
| IO46 | 16 | (下拉) | R7(10K)→GND | - |
| IO47 | 24 | NC (预留) | 悬空 | - |
| IO48 | 25 | NC (预留) | 悬空 | - |
| EN | 3 | (复位) | R1(10K)→3V3, C_EN(1uF)→GND | - |
| 3V3 | 2 | 3V3 | C1(100nF),C2(100nF),C3(10uF)→GND | - |
| GND1 | 1 | GND | - | - |
| GND2 | 40 | GND | - | - |
| EPAD | 41 | GND | - | - |

### 电源网络说明（嘉立创/原理图网络标签用）

以下说明各电源**网络名**的含义，便于在嘉立创等原理图工具中用**网络标签（Net Label）**正确命名。

| 网络名 | 含义 | 是否“输出电压” | 原理图用法 |
|--------|------|----------------|------------|
| **5V** | USB 输入的 5V，**未经过保险丝** | 否，来自 J2(VBUS) | 仅连接：J2 的 VBUS 引脚 → F1.Pin1；该段导线放置标签 `5V` |
| **5V_PROT** | **经 PTC 保险丝 F1 保护后的 5V**，即 F1 的**输出侧**整板 5V 电源轨 | 对 F1 而言是“输出”；对后续芯片而言是“输入电源” | 凡需要从“保护后 5V”取电的节点都标为 `5V_PROT`：F1.Pin2、U4/VCC、U6/VBUS、U7/VCC、WS2812 VDD、充电/状态 LED 限流电阻一侧、去耦电容 C15/C17 等 |
| **VBAT** | 电池电压（未经过开关） | 来自电池/TP4056 | 标在 BT1 正极、U4.Pin5(BAT)、SW1.Pin4(COM)、C_BAT 等 |
| **VBAT_SW** | 经 SW1 开关后的电池电压 | 对 SW1 是输出 | 标在 SW1.Pin2、U5.Pin1(VIN)、U5.Pin3(CE)、C14 等 |
| **3V3** | LDO U5(ME6211) 输出的 3.3V | 是，U5 的输出 | 标在 U5.Pin5(VOUT) 及所有 3.3V 负载 |
| **GND** | 系统公共地 | - | 所有地线统一标 `GND` |

**5V_PROT 小结**：  
- **不是**某颗 IC 的“输出电压”，而是**一根电源网络**的名字。  
- 来源：USB 5V → **F1(PTC 保险丝) Pin1 → Pin2** → 这根线及其所连接的所有节点统称 **5V_PROT**。  
- 在嘉立创原理图中：在 F1 的 Pin2 引出的导线上放置网络标签 **`5V_PROT`**；所有需要从“保护后 5V”供电的元件引脚接到这根线或同样放置 **`5V_PROT`** 标签，即表示同一网络。

**网络标签 vs 电源符号（如 3V3）**：  
- 在嘉立创、KiCad、Altium 等 EDA 中，**网络名称相同即视为同一网络**。因此：  
  - 你在 **LDO 输出** 上放的 **网络标签 `3V3`**  
  - 与在别处使用的 **系统自带电源符号（Power Port）改名为 `3V3`**  
  **会匹配成同一网络**，ERC/DRC 和网表都会把它们连在一起，无需改接法。  
- 若希望原理图“看起来”统一为“从 LDO 供出的 3V3”，可以二选一：  
  1. **保留现状**：LDO 输出用网络标签 `3V3`，其他模块继续用电源符号 `3V3` —— 电气上等价，推荐。  
  2. **统一为网络标签**：删除各处的 3V3 电源符号，在对应引脚上放置 **网络标签 `3V3`**（不改变网络名即可）。  
  3. **统一为电源符号**：把 LDO 输出那根线也改成放置 **电源符号并命名为 `3V3`**（与系统自带封装同名），其他位置继续用电源符号 `3V3`。  
只要网络名一致（均为 `3V3`），三种方式都能正确连接；选择你习惯或规范要求的方式即可。

---

### 电源网络连线表

| 网络名 | 来源 | 连接到 (芯片.引脚) |
|--------|------|-------------------|
| 5V | J2.Pin2(VBUS1), J2.Pin11(VBUS2) | F1.Pin1 |
| 5V_PROT | F1.Pin2 | U4.Pin4(VCC), U4.Pin8(CE), U6.Pin5(VBUS), U7.Pin14(VCC), U7.Pin9(3OE), U7.Pin12(4OE), D1.Pin1(VDD), C15.1, C17.1, C16.1, C11.1, R11.1, R12.1 |
| VBAT | U4.Pin5(BAT), BT1.Pin1(+) | SW1.Pin4(COM), C_BAT.1 |
| VBAT_SW | SW1.Pin2 | U5.Pin1(VIN), U5.Pin3(CE), C14.1 |
| 3V3 | U5.Pin5(VOUT) | U1.Pin2, U2.Pin13(VDD), U2.Pin8(VLOGIC), LCD1.Pin2(VCC), LCD1.Pin8(BLK), J1.Pin4(VCC), R1.2, R2.2, R3.2, R4.2, R5.2, R6.2, C1.1, C2.1, C3.1, C4.1, C5.1, C6.1, C9.1, C10.1 |
| GND | 系统共地 | 所有芯片GND引脚, 所有电容Pin2, U4.Pin1(TEMP★), U4.Pin9(EP), U2.Pin9(AD0), U2.Pin1(CLKIN), U2.Pin11(FSYNC), U7.Pin7, U7.Pin1(1OE), U7.Pin4(2OE), U7.Pin5(2A), U7.Pin8(3A), U7.Pin11(4A), R7.2, R8.2, R9.2, R10.2, J1.Pin1(SHLD), J1.Pin6(VSS) |

### 信号网络连线表

| 网络名 | Pin-A (起点) | Pin-B (终点) | 中间元件 |
|--------|-------------|-------------|---------|
| I2C_SDA | U1.Pin4(IO4) | U2.Pin24(SDA) | R2(4.7K)→3V3 |
| I2C_SCL | U1.Pin5(IO5) | U2.Pin23(SCL) | R3(4.7K)→3V3 |
| MPU6050_INT | U2.Pin12(INT) | U1.Pin6(IO6) | - |
| SPI_SCK_MCU | U1.Pin17(IO9) | R13.Pin1 | - |
| SPI_SCK | R13.Pin2 | LCD1.Pin3(CLK), J1.Pin5(CLK) | - |
| SPI_MOSI_MCU | U1.Pin21(IO13) | R14.Pin1 | - |
| SPI_MOSI | R14.Pin2 | LCD1.Pin4(SDA), J1.Pin8(DAT1) | - |
| SPI_MISO | J1.Pin7(DAT0) | U1.Pin20(IO12) | - |
| SPI_CS_LCD | U1.Pin22(IO14) | LCD1.Pin7(CS1) | - |
| SPI_CS_SD | U1.Pin18(IO10) | J1.Pin3(CMD) | - |
| LCD_DC | U1.Pin19(IO11) | LCD1.Pin6(DC) | - |
| LCD_RST | U1.Pin10(IO17) | LCD1.Pin5(RES) | - |
| (串口调试) | USB CDC | J2 D+/D- → U6 → U1.Pin13/14(IO19/IO20) | 见第五节 |
| USB_DP | J2.Pin6(DP1), J2.Pin8(DP2) | R18.Pin1 | - |
| USB_DP_INT | R18.Pin2 | U6.Pin1(IO1_1), U6.Pin6(IO1_2), U1.Pin14(IO20) | - |
| USB_DN | J2.Pin7(DN1), J2.Pin5(DN2) | R19.Pin1 | - |
| USB_DN_INT | R19.Pin2 | U6.Pin3(IO2_1), U6.Pin4(IO2_2), U1.Pin13(IO19) | - |
| LED_DATA_MCU | U1.Pin23(IO21) | R17.Pin1 | - |
| LED_DATA_BUF | R17.Pin2 | U7.Pin2(1A) | - |
| LED_DATA_5V | U7.Pin3(1Y) | D1.Pin4(DIN) | - |
| KEY_MODE | U1.Pin12(IO8) | R4.1, SW2.1, C18.1 | R4.2→3V3, SW2.2→GND, C18.2→GND |
| KEY_SELECT | U1.Pin15(IO3) | R5.1, SW3.1, C19.1 | R5.2→3V3, SW3.2→GND, C19.2→GND |
| KEY_PLAY | U1.Pin27(IO0) | R6.1, SW4.1, C20.1 | R6.2→3V3, SW4.2→GND, C20.2→GND |
| CHRG_STATUS | U4.Pin7(CHRG) | D4.K(阴极) | R11(1K): 5V_PROT→D4.A |
| STDBY_STATUS | U4.Pin6(STDBY) | D5.K(阴极) | R12(1K): 5V_PROT→D5.A |
| (PROG) | U4.Pin2(PROG) | R10.Pin1 | R10.2→GND |
| (CC1) | J2.Pin5(CC1) | R8.Pin1 | R8.2→GND |
| (CC2) | J2.Pin10(CC2) | R9.Pin1 | R9.2→GND |

---

## 九、元器件封装引脚标号表

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
| 7 | IO7 | GPIO | NC (预留) |
| 8 | IO15 | GPIO | NC (预留) |
| 9 | IO16 | GPIO | NC (预留) |
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
| 24 | IO47 | GPIO | NC (预留) |
| 25 | IO48 | GPIO | NC (预留) |
| 26 | IO45 | GPIO | NC (预留) |
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
| 9 | EP | 散热焊盘 | GND |

**封装**: SOIC-8 (SOP-8), 3.9×4.9mm, 引脚间距1.27mm (9引脚含EP)

---

### 10.3 ME6211 LDO稳压器 (U5)

型号 **ME6211C33M5G-N**，五脚封装（与原理图符号 LDO1 对应）。

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VIN | 输入电压 | VBAT_SW |
| 2 | VSS | 地 | GND |
| 3 | CE | 芯片使能(高有效) | VBAT_SW（与 VIN 同电位，开关打开时使能） |
| 4 | NC | 不连接 | 悬空 |
| 5 | VOUT | 稳压输出 3.3V | 3V3 |

**封装**: SOT-23-5 或等效 5 脚, 2.9×1.6mm

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
| 6 | 2Y | 通道2输出 | **NC (悬空)** |
| 7 | GND | 地 | GND |
| 8 | 3A | 通道3输入 | GND |
| 9 | 3OE | 通道3输出使能(低有效) | 5V_PROT (禁用) |
| 10 | 3Y | 通道3输出 | **NC (悬空)** |
| 11 | 4A | 通道4输入 | GND |
| 12 | 4OE | 通道4输出使能(低有效) | 5V_PROT (禁用) |
| 13 | 4Y | 通道4输出 | **NC (悬空)** |
| 14 | VCC | 电源 | 5V_PROT |

**封装**: SOIC-14, 3.9×8.7mm, 引脚间距1.27mm

---

### 10.6 MPU6050 运动传感器 (U2)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | CLKIN | 外部时钟输入 | GND |
| 2 | NC | 未内部连接 | **NC (悬空)** |
| 3 | NC | 未内部连接 | **NC (悬空)** |
| 4 | NC | 未内部连接 | **NC (悬空)** |
| 5 | NC | 未内部连接 | **NC (悬空)** |
| 6 | AUX_DA | 辅助I2C数据 | **NC (悬空)** |
| 7 | AUX_CL | 辅助I2C时钟 | **NC (悬空)** |
| 8 | VLOGIC | 数字I/O参考电压 | 3V3 + C_VLOGIC(100nF)→GND |
| 9 | AD0 | I2C地址LSB | GND (地址=0x68) |
| 10 | REGOUT | 内部稳压输出 | C_REG(100nF)→GND |
| 11 | FSYNC | 帧同步输入 | GND |
| 12 | INT | 中断输出 | MPU6050_INT |
| 13 | VDD | 主电源 | 3V3 |
| 14 | NC | 未内部连接 | **NC (悬空)** |
| 15 | NC | 未内部连接 | **NC (悬空)** |
| 16 | NC | 未内部连接 | **NC (悬空)** |
| 17 | NC | 未内部连接 | **NC (悬空)** |
| 18 | GND | 地 | GND |
| 19 | RESV | 保留 | **NC (悬空)** |
| 20 | CPOUT | 电荷泵输出 | C_CP(2.2nF)→GND |
| 21 | NC | 未内部连接 | **NC (悬空)** |
| 22 | NC | 未内部连接 | **NC (悬空)** |
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
| 3 | CLK | SPI时钟 | SPI_SCK |
| 4 | SDA | SPI数据 | SPI_MOSI |
| 5 | RES | 复位(低有效) | LCD_RST |
| 6 | DC | 数据/命令选择 | LCD_DC |
| 7 | CS1 | 片选(低有效) | SPI_CS_LCD |
| 8 | BLK | 背光控制 | 3V3 |
| 9 | FS0 | 字库数据输出 | **NC (悬空)** |
| 10 | FCS | 字库IC片选 | **NC (悬空)** |
| 11 | VCC_B | 电源(下排) | 3V3 |
| 12 | GND_B | 地(下排) | GND |
| 13 | BLA | 背光阳极 | **NC (悬空)** |
| 14 | FCS_B | 字库片选(下排) | **NC (悬空)** |
| 15 | FS0_B | 字库数据(下排) | **NC (悬空)** |
| 16 | CLK_B | SPI时钟(下排) | **NC (悬空)** |
| 17 | SDA_B | SPI数据(下排) | **NC (悬空)** |
| 18 | DC_B | 数据/命令(下排) | **NC (悬空)** |
| 19 | RES_B | 复位(下排) | **NC (悬空)** |
| 20 | CS1_B | 片选(下排) | **NC (悬空)** |

**封装**: 2×10 排针, 2.54mm 间距 (20引脚, 上下两排)

---

### 10.8 MicroSD卡座 (J1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | DAT2 | 数据线2 | **NC (悬空)** |
| 2 | CD_DAT3 | 卡检测/数据3 | **NC (悬空)** |
| 3 | CMD | 命令(SPI作CS) | SPI_CS_SD |
| 4 | VDD | 电源 | 3V3 |
| 5 | CLK | SPI时钟 | SPI_SCK |
| 6 | VSS | 地 | GND |
| 7 | DAT0 | 数据0 (SPI MISO) | SPI_MISO |
| 8 | DAT1 | 数据1 (SPI MOSI) | SPI_MOSI |
| 9 | SW_B | 开关B | **NC (悬空)** |
| 10 | NC1 | 未标注 | **NC (悬空)** |
| 11 | SW_A | 开关A | **NC (悬空)** |
| 12 | NC2 | 未标注 | **NC (悬空)** |
| 13 | NC3 | 未标注 | **NC (悬空)** |
| 14 | NC4 | 未标注 | **NC (悬空)** |

**封装**: Hirose DM3AT-SF-PEJM5, 14引脚

---

### 10.9 串口调试与固件烧录（USB 复用）

串口调试与固件烧录/升级均通过 **现有 USB (J2)** 完成，无需独立 UART 排针或 USB 转 TTL 模块。**当前项目为“USB 连电脑”方式做调试与固件更新，非无线 OTA。**

- **路径**: J2(Type-C) D+/D- → U6(ESD) → R18/R19(22Ω) → U1.Pin14(IO20)/Pin13(IO19)
- **串口**: ESP32-S3 内置 USB Serial/JTAG，连接电脑后枚举为 CDC 串口；`Serial` 默认经此 USB 输出。
- **烧录**: 同一 USB 支持进入下载模式，用 Arduino“上传”、`idf.py flash`、esptool 等通过 Type-C 线烧录/升级固件。
- **使用**: Type-C 线连接魔杖与电脑 → 串口监视器查看打印，或运行烧录工具更新固件。

---

### 10.10 WS2812B RGB LED (D1，单颗)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | VDD | 电源 | 5V_PROT |
| 2 | DOUT | 数据输出 | NC (悬空，无级联) |
| 3 | GND | 地 | GND |
| 4 | DIN | 数据输入 | LED_DATA_5V (经 U7 电平转换) |

**封装**: PLCC-4, 5.0×5.0mm, 引脚间距3.2mm

---

### 10.11 USB Type-C 母座 (J2)

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

### 10.12 PTC自恢复保险丝 (F1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 输入端 | 5V |
| 2 | 2 | 输出端 | 5V_PROT |

**封装**: SMD 1206, 3.2×1.6mm

**规格**: 750mA保持电流, 1.5A触发电流, 13.2V最大电压

---

### 10.13 LED指示灯 (D4/D5)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | A | 阳极 | R11/R12(1KΩ)→5V_PROT |
| 2 | K | 阴极 | CHRG_STATUS/STDBY_STATUS |

**封装**: SMD 0805, 2.0×1.2mm

**颜色**: D4=红色(充电), D5=绿色(充满)

---

### 10.14 电源开关 (SW1)

型号 **MSK12C02**，四脚 **SP3T**（单刀三掷）：**Pin4 为公共端(COM)**，Pin1/Pin2/Pin3 为三档位。本电路仅用其中一档接 VBAT_SW（如 Pin2 为“开”），其余两档悬空。

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 档位1 | OFF 位 | NC (悬空) |
| 2 | 档位2 | ON 位 | VBAT_SW |
| 3 | 档位3 | OFF 位 | NC (悬空) |
| 4 | COM | 公共端 | VBAT（电池正） |

**注意**：若原理图符号内部画有 GND 标识，多为库符号误绘或机械地；**切勿将 Pin4(COM) 接 GND**，否则会短路电池。

**封装**: MSK12C02, SMD 滑动开关, 4 脚

**规格**: SP3T, 0.3A, 6V DC

---

### 10.15 按键开关 (SW2/SW3/SW4)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | 1 | 按键端1 | KEY_MODE/SELECT/PLAY |
| 2 | 2 | 按键端2 | GND |

**封装**: SMD按键开关, 2引脚

---

### 10.16 电阻 (R1-R17)

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
- R13/R14: 33Ω (SPI SCK/MOSI 阻尼)
- R17: 100Ω (LED数据串联)
- R18/R19: 22Ω (USB数据串联)

---

### 10.17 电容 (C1-C20, C_EN, C_BAT, C_CP, C_REG)

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
- C1/C2/C4/C5/C9/C10/C11/C16: 100nF (去耦)
- C3/C6/C14/C15/C17: 10uF (滤波)
- C_BAT: 10uF (TP4056 BAT去耦)
- C_EN: 1uF (ESP32 EN复位延迟)
- C_CP: 2.2nF (MPU6050电荷泵)
- C_REG: 100nF (MPU6050稳压器)
- C18/C19/C20: 100nF (按键去抖)
- C17: 22uF (VBUS大容量滤波)

---

### 10.18 电池 (BT1)

| 封装Pin | 名称 | 功能 | 连接 |
|---------|------|------|------|
| 1 | + | 正极 | VBAT |
| 2 | - | 负极 | GND |

**规格**: 603040, 3.7V, 800mAh, 锂电池

---

*v2.3 所有引脚编号严格按各芯片数据手册。可作为KiCad绘制原理图和PCB布局的完整参考。*
