"""
赛博魔杖 (CyberWand) 完整电路连接描述 v2.4
使用 SKiDL 描述所有硬件连接

v2.4 变更: 去掉 DFPlayer 音频模块与扬声器；串口/烧录复用 USB；可编程 LED 仅保留一颗 WS2812B(D1)。

v2.3 修复清单 (电气属性验证):
  ★ 致命修复: ME6211 SOT-23 Pin2/Pin3反了! 数据手册: Pin1=VIN,Pin2=VOUT,Pin3=VSS
  ★ 致命修复: TP4056 TEMP必须接GND禁用! 接VCC会导致TEMP/VIN=100%>80%→充电永久暂停

v2.2 修复清单 (芯片手册级审查):
  ★ 修复: MPU6050引脚映射 (按QFN-24数据手册重写: VDD=Pin13, VLOGIC=Pin8, CPOUT=Pin20)
  ★ 修复: MPU6050 CPOUT(Pin20) 必须接2.2nF到GND (电荷泵)
  ★ 修复: MPU6050 REGOUT(Pin10) 必须接100nF到GND (内部稳压)
  ★ 修复: MPU6050 CLKIN(Pin1) 必须接GND (不用外部时钟)
  ★ 修复: MPU6050 FSYNC(Pin11) 必须接GND (不用帧同步)
  ★ 修复: ESP32 EN引脚增加1uF电容到GND (电源上电复位延迟)
  ★ 修复: TP4056 BAT增加10uF去耦电容 (电池端稳定)
  ★ 修复: DFPlayer RX增加1KΩ串联保护电阻

v2.1 修复清单:
  - TP4056引脚映射按数据手册 (TEMP/PROG/GND/VCC/BAT/STDBY/CHRG/CE)
  - CHRG/STDBY LED开漏正确接法 (VCC→R→LED→引脚)
  - 电源开关NC悬空 (防电池短路)
  - TEMP接GND禁用温度监测 (v2.3修正: 接VCC会阻止充电)
  - USB D+/D-连接ESP32原生USB

v2.0 改进清单:
  1-10: ESD/PTC/电平转换/阻尼电阻/去抖电容等 (见v2.0注释)
"""

from skidl import Net, generate_netlist, ERC

from esp32_s3_wroom import ESP32_S3_WROOM
from mpu6050_part import MPU6050
from hs20s010b_lcd_part import HS20S010B_LCD
from microsd_socket_part import MICROSD_SOCKET
from ws2812b_part import WS2812B
from tp4056_part import TP4056
from me6211_part import ME6211
from usb_type_c_part import USB_TYPE_C
from battery_603040 import BATTERY_603040
from led_part import LED_RED, LED_GREEN
from usblc6_2sc6_part import USBLC6_2SC6
from sn74ahct125_part import SN74AHCT125
from ptc_fuse_part import PTC_FUSE_500MA
from power_switch_part import POWER_SWITCH
from passive_parts import (R_10K, R_4K7, R_2K, R_5K1, R_1K,
                           R_33, R_100, R_22,
                           C_2N2, C_100N, C_10U, C_1U, C_22U,
                           SWITCH)
import os

# ============================================================
# 1. 元器件实例
# ============================================================

mcu = ESP32_S3_WROOM()
imu = MPU6050()
lcd = HS20S010B_LCD()
sd_card = MICROSD_SOCKET()
led1 = WS2812B()   # 仅一颗可编程 RGB LED

usb_conn = USB_TYPE_C()
battery = BATTERY_603040()
charger = TP4056()
ldo = ME6211()

usb_esd = USBLC6_2SC6()
ptc_fuse = PTC_FUSE_500MA()
level_shifter = SN74AHCT125()
pwr_switch = POWER_SWITCH()

key_mode = SWITCH()
key_select = SWITCH()
key_play = SWITCH()
led_charging = LED_RED()
led_charged = LED_GREEN()

# --- 电阻 ---
r_en_pullup = R_10K()
r_i2c_sda_pullup = R_4K7()
r_i2c_scl_pullup = R_4K7()
r_key_mode_pullup = R_10K()
r_key_select_pullup = R_10K()
r_key_play_pullup = R_10K()
r_io46_pulldown = R_10K()
r_cc1 = R_5K1()
r_cc2 = R_5K1()
r_prog = R_2K()
r_led_red = R_1K()
r_led_green = R_1K()
r_spi_sck_damp = R_33()
r_spi_mosi_damp = R_33()
r_led_data_series = R_100()
r_usb_dp = R_22()
r_usb_dn = R_22()
# --- 电容 (20→24个, 新增MPU6050+EN+BAT+VLOGIC) ---
c_mcu_1 = C_100N()
c_mcu_2 = C_100N()
c_mcu_3 = C_10U()
c_en_reset = C_1U()             # ★ v2.2新增: ESP32 EN上电复位延迟
c_imu = C_100N()                # MPU6050 VDD去耦
c_imu_vlogic = C_100N()         # ★ 新增: MPU6050 VLOGIC去耦 (数字I/O参考电压)
c_imu_cpout = C_2N2()           # ★ v2.2新增: MPU6050 CPOUT电荷泵 2.2nF
c_imu_regout = C_100N()         # ★ v2.2新增: MPU6050 REGOUT内部稳压 100nF
c_lcd_1 = C_100N()
c_lcd_2 = C_10U()
c_led1 = C_100N()   # D1 去耦
c_ldo_in = C_10U()
c_ldo_out = C_10U()
c_usb = C_10U()
c_level_shifter = C_100N()
c_vbus_bulk = C_22U()
c_bat = C_10U()                 # ★ v2.2新增: TP4056 BAT端去耦
c_key_mode_debounce = C_100N()
c_key_select_debounce = C_100N()
c_key_play_debounce = C_100N()

# ============================================================
# 2. 电源网络
# ============================================================

vcc_5v = Net('5V')
vcc_5v_prot = Net('5V_PROT')
vcc_bat = Net('VBAT')
vcc_bat_sw = Net('VBAT_SW')
vcc_3v3 = Net('3V3')
gnd = Net('GND')

# ============================================================
# 3. USB Type-C (ESD+过流保护)
# ============================================================
# ★ 更新：使用16引脚Type-C连接器 (TYPE-C 16PIN 2MD(073))
# 实际封装：左侧12引脚 + 右侧2个SHELL引脚

# VBUS引脚（正反插时都会连接）
usb_conn['VBUS1'] += vcc_5v    # Pin2: VBUS
usb_conn['VBUS2'] += vcc_5v    # Pin11: VBUS

ptc_fuse[1] += vcc_5v
ptc_fuse[2] += vcc_5v_prot

# GND引脚（所有GND引脚都连接到系统GND）
usb_conn['GND1'] += gnd         # Pin1: GND
usb_conn['GND2'] += gnd         # Pin12: GND
usb_conn['SHELL1'] += gnd       # Pin13: SHELL (金属外壳)
usb_conn['SHELL2'] += gnd       # Pin14: SHELL (金属外壳)

# CC配置通道（用于检测连接和方向）
usb_conn['CC1'] += r_cc1[1]     # Pin4: CC1
r_cc1[2] += gnd
usb_conn['CC2'] += r_cc2[1]     # Pin10: CC2
r_cc2[2] += gnd

usb_esd['VBUS'] += vcc_5v_prot
usb_esd['GND'] += gnd

usb_d_plus = Net('USB_DP')
usb_d_minus = Net('USB_DN')
usb_dp_int = Net('USB_DP_INT')
usb_dn_int = Net('USB_DN_INT')

# USB 2.0数据引脚（正反插时都会连接）
# A侧：DP1(Pin6), DN1(Pin7)
# B侧：DP2(Pin8), DN2(Pin5)
usb_conn['DP1'] += usb_d_plus   # Pin6: D+ (A侧)
usb_conn['DP2'] += usb_d_plus   # Pin8: D+ (B侧)
usb_conn['DN1'] += usb_d_minus  # Pin7: D- (A侧)
usb_conn['DN2'] += usb_d_minus  # Pin5: D- (B侧)

# SBU辅助信号（未使用，可悬空）
# usb_conn['SBU1'] += ...  # Pin9: SBU1 (未使用)
# usb_conn['SBU2'] += ...  # Pin3: SBU2 (未使用)

r_usb_dp[1] += usb_d_plus
r_usb_dp[2] += usb_dp_int
usb_esd['IO1_1'] += usb_dp_int
usb_esd['IO1_2'] += usb_dp_int

r_usb_dn[1] += usb_d_minus
r_usb_dn[2] += usb_dn_int
usb_esd['IO2_1'] += usb_dn_int
usb_esd['IO2_2'] += usb_dn_int

mcu['IO19'] += usb_dn_int    # ESP32原生 USB D-
mcu['IO20'] += usb_dp_int    # ESP32原生 USB D+

c_usb[1] += vcc_5v_prot
c_usb[2] += gnd
c_vbus_bulk[1] += vcc_5v_prot
c_vbus_bulk[2] += gnd

# ============================================================
# 4. TP4056 充电管理 (引脚按数据手册SOIC-8)
# ============================================================

charger['VCC'] += vcc_5v_prot     # Pin4
charger['GND'] += gnd             # Pin3
charger['BAT'] += vcc_bat         # Pin5
charger['CE'] += vcc_5v_prot      # Pin8
charger['TEMP'] += gnd             # Pin1: TEMP接GND禁用温度监测
charger['EP'] += gnd               # Pin9: EP散热焊盘连接到GND
# ★ 数据手册: TEMP接GND禁用! 若接VCC, TEMP/VIN=100%>80%阈值, 充电永久暂停!

charger['PROG'] += r_prog[1]      # Pin2: ICHG=1000/RPROG=500mA
r_prog[2] += gnd

# ★ v2.2: BAT端去耦电容 (数据手册要求)
c_bat[1] += vcc_bat
c_bat[2] += gnd

# CHRG/STDBY LED (开漏接法: VCC→R→LED→引脚)
chrg_net = Net('CHRG_STATUS')
charger['CHRG'] += chrg_net
r_led_red[1] += vcc_5v_prot
r_led_red[2] += led_charging['A']
led_charging['K'] += chrg_net

stdby_net = Net('STDBY_STATUS')
charger['STDBY'] += stdby_net
r_led_green[1] += vcc_5v_prot
r_led_green[2] += led_charged['A']
led_charged['K'] += stdby_net

# 电池
battery['+'] += vcc_bat
battery['-'] += gnd

# 电源开关 (NC悬空!)
pwr_switch['COM'] += vcc_bat
pwr_switch['NO'] += vcc_bat_sw

# ME6211 LDO
ldo['VIN'] += vcc_bat_sw          # Pin1
ldo['VOUT'] += vcc_3v3            # Pin2 (★v2.3修复: 原来Pin2/Pin3反了!)
ldo['VSS'] += gnd                 # Pin3

c_ldo_in[1] += vcc_bat_sw
c_ldo_in[2] += gnd
c_ldo_out[1] += vcc_3v3
c_ldo_out[2] += gnd

# ============================================================
# 5. ESP32-S3 主控
# ============================================================

mcu['3V3'] += vcc_3v3
mcu['GND1'] += gnd
mcu['GND2'] += gnd
mcu['EPAD'] += gnd

# ★ v2.2: EN引脚 RC复位电路 (10K上拉 + 1uF到GND)
# 数据手册要求: 1uF确保上电时EN延迟拉高, 保证可靠复位
mcu['EN'] += r_en_pullup[1]
r_en_pullup[2] += vcc_3v3
c_en_reset[1] += r_en_pullup[1]   # EN网络
c_en_reset[2] += gnd              # 1uF到GND

mcu['IO46'] += r_io46_pulldown[1]
r_io46_pulldown[2] += gnd

c_mcu_1[1] += vcc_3v3
c_mcu_1[2] += gnd
c_mcu_2[1] += vcc_3v3
c_mcu_2[2] += gnd
c_mcu_3[1] += vcc_3v3
c_mcu_3[2] += gnd

# ============================================================
# 6. MPU6050 (I2C) ★ v2.2全面修复
# ============================================================

# 电源 (按数据手册: VDD=Pin13, VLOGIC=Pin8)
imu['VDD'] += vcc_3v3             # Pin13: 主电源
imu['VLOGIC'] += vcc_3v3          # Pin8: 数字I/O参考电压
imu['GND'] += gnd                 # Pin18: 地

# I2C
i2c_sda = Net('I2C_SDA')
i2c_scl = Net('I2C_SCL')

mcu['IO4'] += i2c_sda
mcu['IO5'] += i2c_scl
imu['SDA'] += i2c_sda             # Pin24
imu['SCL'] += i2c_scl             # Pin23

r_i2c_sda_pullup[1] += i2c_sda
r_i2c_sda_pullup[2] += vcc_3v3
r_i2c_scl_pullup[1] += i2c_scl
r_i2c_scl_pullup[2] += vcc_3v3

imu['AD0'] += gnd                 # Pin9: 地址=0x68

mpu_int = Net('MPU6050_INT')
imu['INT'] += mpu_int             # Pin12
mcu['IO6'] += mpu_int

# ★ v2.2: 数据手册强制要求的引脚连接
imu['CLKIN'] += gnd               # Pin1: 不用外部时钟→接GND
imu['FSYNC'] += gnd               # Pin11: 不用帧同步→接GND

# ★ v2.2: 数据手册强制要求的外部电容
c_imu[1] += vcc_3v3               # VDD去耦 100nF
c_imu[2] += gnd

c_imu_vlogic[1] += imu['VLOGIC']  # Pin8: VLOGIC去耦 100nF→GND (数字I/O参考电压)
c_imu_vlogic[2] += gnd

c_imu_cpout[1] += imu['CPOUT']    # Pin20: 电荷泵 2.2nF→GND
c_imu_cpout[2] += gnd

c_imu_regout[1] += imu['REGOUT']  # Pin10: 内部稳压 100nF→GND
c_imu_regout[2] += gnd

# ============================================================
# 7. LCD (SPI + 阻尼电阻)
# ============================================================
# ★ 更新：使用20引脚LCD，连接上排引脚（Pin1-10）

lcd['VCC'] += vcc_3v3      # Pin2: VCC (上排)
lcd['GND'] += gnd          # Pin1: GND (上排)
# 下排的VCC_B和GND_B也可以连接，但通常只连接上排即可
lcd['VCC_B'] += vcc_3v3    # Pin11: VCC (下排，可选)
lcd['GND_B'] += gnd        # Pin12: GND (下排，可选)

spi_sck = Net('SPI_SCK')
spi_mosi = Net('SPI_MOSI')
spi_miso = Net('SPI_MISO')
spi_cs_lcd = Net('SPI_CS_LCD')
lcd_dc = Net('LCD_DC')
lcd_rst = Net('LCD_RST')

spi_sck_mcu = Net('SPI_SCK_MCU')
mcu['IO9'] += spi_sck_mcu
r_spi_sck_damp[1] += spi_sck_mcu
r_spi_sck_damp[2] += spi_sck

spi_mosi_mcu = Net('SPI_MOSI_MCU')
mcu['IO13'] += spi_mosi_mcu
r_spi_mosi_damp[1] += spi_mosi_mcu
r_spi_mosi_damp[2] += spi_mosi

mcu['IO12'] += spi_miso   # MISO 直连（无串联电阻）
mcu['IO14'] += spi_cs_lcd
mcu['IO11'] += lcd_dc
mcu['IO17'] += lcd_rst

# 连接上排引脚（Pin1-10）
lcd['CLK'] += spi_sck      # Pin3: CLK (SPI时钟)
lcd['SDA'] += spi_mosi     # Pin4: SDA (SPI数据)
lcd['RES'] += lcd_rst      # Pin5: RES (复位)
lcd['DC'] += lcd_dc        # Pin6: DC (数据/命令)
lcd['CS1'] += spi_cs_lcd   # Pin7: CS1 (片选)
lcd['BLK'] += vcc_3v3      # Pin8: BLK (背光控制)
# Pin9(FS0) 和 Pin10(FCS) 未使用，可悬空

c_lcd_1[1] += vcc_3v3
c_lcd_1[2] += gnd
c_lcd_2[1] += vcc_3v3
c_lcd_2[2] += gnd

# ============================================================
# 8. MicroSD (SPI共享)
# ============================================================
# ★ 更新：使用14引脚SD卡座 DM3AT-SF-PEJM5

sd_card['VDD'] += vcc_3v3  # Pin4: VDD (电源)
sd_card['VSS'] += gnd      # Pin6: VSS (地)

spi_cs_sd = Net('SPI_CS_SD')
# SPI模式连接：
# CMD(Pin3) → CS (片选)
# CLK(Pin5) → SCK (时钟)
# DAT0(Pin7) → MISO (主入从出)
# DAT1(Pin8) → MOSI (主出从入)
sd_card['CMD'] += spi_cs_sd    # Pin3: CMD (SPI模式下用作CS)
sd_card['CLK'] += spi_sck      # Pin5: CLK (SPI时钟)
sd_card['DAT0'] += spi_miso     # Pin7: DAT0 (SPI MISO)，直连 MCU
sd_card['DAT1'] += spi_mosi     # Pin8: DAT1 (SPI MOSI)
mcu['IO10'] += spi_cs_sd

# 卡检测（可选）
# sd_card['CD_DAT3'] += ...     # Pin2: CD/DAT3 (卡检测)

# 未使用的引脚
# Pin1(DAT2), Pin8(DAT1), Pin9(SW_B), Pin10-14(NC) 未使用

# ============================================================
# 9. 串口调试：USB 复用 (无需独立 UART 排针)
# ============================================================
# 使用现有 Type-C (J2) 连接电脑即可：ESP32-S3 内置 USB Serial/JTAG，
# 固件中 Serial 输出通过 USB CDC 到电脑，无需外接 USB 转 TTL。
# IO47/IO48 不接调试排针，留作 NC 或其它用途。

# ============================================================
# 10. WS2812B (电平转换 + 独立去耦)
# ============================================================

level_shifter['VCC'] += vcc_5v_prot
level_shifter['GND'] += gnd

level_shifter['1OE'] += gnd
level_shifter['2OE'] += gnd
level_shifter['3OE'] += vcc_5v_prot
level_shifter['4OE'] += vcc_5v_prot

led_data_mcu = Net('LED_DATA_MCU')
led_data_buf = Net('LED_DATA_BUF')
led_data_out = Net('LED_DATA_5V')

mcu['IO21'] += led_data_mcu
r_led_data_series[1] += led_data_mcu
r_led_data_series[2] += led_data_buf
level_shifter['1A'] += led_data_buf
level_shifter['1Y'] += led_data_out

level_shifter['2A'] += gnd
level_shifter['3A'] += gnd
level_shifter['4A'] += gnd

c_level_shifter[1] += vcc_5v_prot
c_level_shifter[2] += gnd

led1['VDD'] += vcc_5v_prot
led1['GND'] += gnd
led1['DIN'] += led_data_out
# D1.Pin2(DOUT) 悬空 (单颗 LED，无级联)

c_led1[1] += vcc_5v_prot
c_led1[2] += gnd

# ============================================================
# 11. 按键 (硬件去抖)
# ============================================================

key_mode_net = Net('KEY_MODE')
mcu['IO8'] += key_mode_net
key_mode_net += r_key_mode_pullup[1]
r_key_mode_pullup[2] += vcc_3v3
key_mode_net += key_mode[1]
key_mode[2] += gnd
c_key_mode_debounce[1] += key_mode_net
c_key_mode_debounce[2] += gnd

key_select_net = Net('KEY_SELECT')
mcu['IO3'] += key_select_net
key_select_net += r_key_select_pullup[1]
r_key_select_pullup[2] += vcc_3v3
key_select_net += key_select[1]
key_select[2] += gnd
c_key_select_debounce[1] += key_select_net
c_key_select_debounce[2] += gnd

key_play_net = Net('KEY_PLAY')
mcu['IO0'] += key_play_net
key_play_net += r_key_play_pullup[1]
r_key_play_pullup[2] += vcc_3v3
key_play_net += key_play[1]
key_play[2] += gnd
c_key_play_debounce[1] += key_play_net
c_key_play_debounce[2] += gnd

# ============================================================
# 12. 生成网表
# ============================================================

if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    print("执行ERC...")
    ERC()

    netlist_path = os.path.join(output_dir, 'cyberwand_netlist.net')
    print(f"\n生成网表...")
    generate_netlist(file_=netlist_path)
    print(f"网表已生成: {netlist_path}")
    print("\nv2.4 电路设计完成! (无音频，可编程LED仅D1)")
