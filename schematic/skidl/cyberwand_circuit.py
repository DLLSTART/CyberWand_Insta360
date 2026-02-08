"""
赛博魔杖 (CyberWand) 完整电路连接描述 v2.0
使用 SKiDL 描述所有硬件连接

v2.0 改进清单:
  1. USB ESD保护 (USBLC6-2SC6)
  2. USB VBUS过流保护 (PTC自恢复保险丝 500mA)
  3. WS2812B电平转换 (SN74AHCT125)
  4. 总电源开关 (滑动开关)
  5. SPI/I2S阻尼电阻 (信号完整性)
  6. USB数据线串联电阻 (阻抗匹配)
  7. WS2812B数据线串联电阻
  8. 按键硬件去抖电容
  9. 每个WS2812B独立去耦电容
  10. DFPlayer增加100nF高频去耦
  11. TP4056 CE正确连接
"""

from skidl import Net, generate_netlist, ERC

# 导入所有元器件模板
from esp32_s3_wroom import ESP32_S3_WROOM
from mpu6050_part import MPU6050
from hs20s010b_lcd_part import HS20S010B_LCD
from microsd_socket_part import MICROSD_SOCKET
from dfplayer_mini_part import DFPLAYER_MINI
from inmp441_part import INMP441
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
                           C_100N, C_10U, C_1U, C_22U,
                           SWITCH, SPEAKER)
import os

# ============================================================
# 1. 创建所有元器件实例
# ============================================================

# 主控芯片
mcu = ESP32_S3_WROOM()

# 传感器和外设
imu = MPU6050()              # 6轴运动传感器
lcd = HS20S010B_LCD()        # 2.0寸 TFT LCD显示屏
sd_card = MICROSD_SOCKET()   # MicroSD卡座
audio_player = DFPLAYER_MINI()  # 音频播放模块
microphone = INMP441()       # MEMS麦克风
led1 = WS2812B()             # RGB LED 1
led2 = WS2812B()             # RGB LED 2
led3 = WS2812B()             # RGB LED 3

# 电源管理
usb_conn = USB_TYPE_C()      # Type-C接口
battery = BATTERY_603040()   # 锂电池
charger = TP4056()           # 充电管理芯片
ldo = ME6211()               # LDO稳压芯片

# ★ 新增保护组件
usb_esd = USBLC6_2SC6()      # USB ESD保护
ptc_fuse = PTC_FUSE_500MA()  # USB过流保护保险丝
level_shifter = SN74AHCT125()  # WS2812B电平转换器
pwr_switch = POWER_SWITCH()  # 总电源开关

# 按键
key_mode = SWITCH()           # 模式选择按键
key_select = SWITCH()         # 手势选择按键
key_play = SWITCH()           # 播放/确认按键

# 扬声器
speaker = SPEAKER()

# 充电指示灯
led_charging = LED_RED()      # 红色LED - 充电中
led_charged = LED_GREEN()     # 绿色LED - 充满

# 被动元器件 - 上拉电阻
r_en_pullup = R_10K()         # ESP32 EN引脚上拉
r_i2c_sda_pullup = R_4K7()   # I2C SDA上拉
r_i2c_scl_pullup = R_4K7()   # I2C SCL上拉
r_key_mode_pullup = R_10K()   # 按键1上拉
r_key_select_pullup = R_10K() # 按键2上拉
r_key_play_pullup = R_10K()   # 按键3上拉

# 下拉电阻
r_io46_pulldown = R_10K()     # IO46下拉（纯输入引脚）

# Type-C CC配置电阻
r_cc1 = R_5K1()
r_cc2 = R_5K1()

# TP4056充电电流设置电阻
r_prog = R_2K()               # 500mA充电电流

# LED 限流电阻
r_led_red = R_1K()
r_led_green = R_1K()

# ★ 新增阻尼电阻 (信号完整性)
r_spi_sck_damp = R_33()       # SPI SCK 阻尼
r_spi_mosi_damp = R_33()      # SPI MOSI 阻尼
r_i2s_sck_damp = R_33()       # I2S SCK 阻尼
r_i2s_ws_damp = R_33()        # I2S WS 阻尼
r_led_data_series = R_100()   # WS2812B 数据线串联电阻

# ★ USB数据线串联电阻 (阻抗匹配)
r_usb_dp = R_22()
r_usb_dn = R_22()

# 去耦电容
c_mcu_1 = C_100N()            # ESP32去耦1
c_mcu_2 = C_100N()            # ESP32去耦2
c_mcu_3 = C_10U()             # ESP32去耦3
c_imu = C_100N()              # MPU6050去耦
c_lcd_1 = C_100N()            # LCD去耦1
c_lcd_2 = C_10U()             # LCD去耦2
c_audio_1 = C_10U()           # DFPlayer去耦(低频)
c_audio_2 = C_100N()          # DFPlayer去耦(高频) ★ 新增
c_mic = C_100N()              # INMP441去耦
c_led1 = C_100N()             # WS2812B去耦1 ★ 每个LED独立去耦
c_led2 = C_100N()             # WS2812B去耦2
c_led3 = C_100N()             # WS2812B去耦3
c_ldo_in = C_10U()            # ME6211输入电容
c_ldo_out = C_10U()           # ME6211输出电容
c_usb = C_10U()               # USB滤波电容
c_level_shifter = C_100N()    # 74AHCT125去耦 ★ 新增
c_vbus_bulk = C_22U()         # VBUS大容量储能 ★ 新增

# ★ 按键去抖电容 (硬件去抖)
c_key_mode_debounce = C_100N()
c_key_select_debounce = C_100N()
c_key_play_debounce = C_100N()

# ============================================================
# 2. 创建电源网络
# ============================================================

vcc_5v = Net('5V')             # 5V电源网络 (USB VBUS)
vcc_5v_prot = Net('5V_PROT')  # PTC保险丝后的5V (保护后)
vcc_bat = Net('VBAT')          # 电池电压网络
vcc_bat_sw = Net('VBAT_SW')   # 开关后的电池电压
vcc_3v3 = Net('3V3')          # 3.3V电源网络
gnd = Net('GND')               # 地网络

# ============================================================
# 3. USB Type-C 接口连接 (含ESD+过流保护)
# ============================================================

# Type-C VBUS → PTC保险丝 → 保护后5V
usb_conn['VBUS_A4'] += vcc_5v
usb_conn['VBUS_B4'] += vcc_5v

# ★ PTC自恢复保险丝: VBUS → F1 → 5V_PROT
ptc_fuse[1] += vcc_5v
ptc_fuse[2] += vcc_5v_prot

# Type-C GND
usb_conn['GND_A1'] += gnd
usb_conn['GND_B1'] += gnd
usb_conn['GND_A12'] += gnd
usb_conn['GND_B12'] += gnd
usb_conn['SHIELD'] += gnd

# Type-C CC引脚配置（Sink模式，5.1K下拉）
usb_conn['CC1'] += r_cc1[1]
r_cc1[2] += gnd
usb_conn['CC2'] += r_cc2[1]
r_cc2[2] += gnd

# ★ USB ESD保护 (USBLC6-2SC6)
usb_esd['VBUS'] += vcc_5v_prot   # 接保护后的5V
usb_esd['GND'] += gnd

# USB数据线: Type-C → 串联电阻 → ESD保护 → ESP32
usb_d_plus = Net('USB_DP')
usb_d_minus = Net('USB_DN')
usb_dp_int = Net('USB_DP_INT')    # ESD保护后的内部节点
usb_dn_int = Net('USB_DN_INT')

usb_conn['DP1'] += usb_d_plus
usb_conn['DP2'] += usb_d_plus
usb_conn['DN1'] += usb_d_minus
usb_conn['DN2'] += usb_d_minus

# USB D+ 路径: 连接器 → 串联22Ω → ESD保护 → MCU
r_usb_dp[1] += usb_d_plus
r_usb_dp[2] += usb_dp_int
usb_esd['IO1_1'] += usb_dp_int
usb_esd['IO1_2'] += usb_dp_int

# USB D- 路径
r_usb_dn[1] += usb_d_minus
r_usb_dn[2] += usb_dn_int
usb_esd['IO2_1'] += usb_dn_int
usb_esd['IO2_2'] += usb_dn_int

# USB VBUS储能+滤波
c_usb[1] += vcc_5v_prot
c_usb[2] += gnd
c_vbus_bulk[1] += vcc_5v_prot
c_vbus_bulk[2] += gnd

# ============================================================
# 4. 电源管理电路连接 (含电源开关)
# ============================================================

# TP4056 充电管理芯片连接 (使用保护后的5V)
charger['VIN'] += vcc_5v_prot
charger['GND'] += gnd
charger['BAT'] += vcc_bat
charger['CE'] += vcc_5v_prot     # CE接VBUS，有USB插入时自动充电
charger['RST'] += vcc_5v_prot    # RST接高电平

# TP4056 充电电流设置
charger['PROG'] += r_prog[1]
r_prog[2] += gnd

# TP4056 充电指示灯
charger['CHRG'] += r_led_red[1]
r_led_red[2] += led_charging['A']
led_charging['K'] += gnd

charger['STDBY'] += r_led_green[1]
r_led_green[2] += led_charged['A']
led_charged['K'] += gnd

# 锂电池连接
battery['+'] += vcc_bat
battery['-'] += gnd

# ★ 电源总开关: 电池 → 开关 → 系统
pwr_switch['COM'] += vcc_bat       # 公共端接电池
pwr_switch['NO'] += vcc_bat_sw     # 常开端接系统 (推到ON位置时导通)
pwr_switch['NC'] += gnd            # 常闭端接地 (可选: NC悬空也行)

# ME6211 LDO稳压: 开关后电池电压 → LDO → 3.3V
ldo['VIN'] += vcc_bat_sw
ldo['GND'] += gnd
ldo['VOUT'] += vcc_3v3

# LDO去耦电容
c_ldo_in[1] += vcc_bat_sw
c_ldo_in[2] += gnd
c_ldo_out[1] += vcc_3v3
c_ldo_out[2] += gnd

# ============================================================
# 5. ESP32-S3 主控芯片连接
# ============================================================

# 电源连接
mcu['3V3'] += vcc_3v3
mcu['GND1'] += gnd
mcu['GND2'] += gnd
mcu['EPAD'] += gnd

# EN引脚上拉
mcu['EN'] += r_en_pullup[1]
r_en_pullup[2] += vcc_3v3

# IO46下拉
mcu['IO46'] += r_io46_pulldown[1]
r_io46_pulldown[2] += gnd

# ESP32去耦电容 (靠近芯片放置)
c_mcu_1[1] += vcc_3v3
c_mcu_1[2] += gnd
c_mcu_2[1] += vcc_3v3
c_mcu_2[2] += gnd
c_mcu_3[1] += vcc_3v3
c_mcu_3[2] += gnd

# ============================================================
# 6. MPU6050 陀螺仪传感器连接（I2C）
# ============================================================

imu['VCC'] += vcc_3v3
imu['GND'] += gnd
imu['VLOGIC'] += vcc_3v3

i2c_sda = Net('I2C_SDA')
i2c_scl = Net('I2C_SCL')

mcu['IO4'] += i2c_sda
mcu['IO5'] += i2c_scl
imu['SDA'] += i2c_sda
imu['SCL'] += i2c_scl

r_i2c_sda_pullup[1] += i2c_sda
r_i2c_sda_pullup[2] += vcc_3v3
r_i2c_scl_pullup[1] += i2c_scl
r_i2c_scl_pullup[2] += vcc_3v3

imu['AD0'] += gnd

mpu_int = Net('MPU6050_INT')
imu['INT'] += mpu_int
mcu['IO6'] += mpu_int

c_imu[1] += vcc_3v3
c_imu[2] += gnd

# ============================================================
# 7. HS20S010B LCD 显示屏连接（SPI + 阻尼电阻）
# ============================================================

lcd['VCC'] += vcc_3v3
lcd['GND'] += gnd

# SPI信号网络
spi_sck = Net('SPI_SCK')
spi_mosi = Net('SPI_MOSI')
spi_miso = Net('SPI_MISO')
spi_cs_lcd = Net('SPI_CS_LCD')
lcd_dc = Net('LCD_DC')
lcd_rst = Net('LCD_RST')

# ★ SPI时钟通过阻尼电阻
spi_sck_mcu = Net('SPI_SCK_MCU')   # MCU侧
mcu['IO9'] += spi_sck_mcu
r_spi_sck_damp[1] += spi_sck_mcu
r_spi_sck_damp[2] += spi_sck

# ★ SPI MOSI通过阻尼电阻
spi_mosi_mcu = Net('SPI_MOSI_MCU')
mcu['IO13'] += spi_mosi_mcu
r_spi_mosi_damp[1] += spi_mosi_mcu
r_spi_mosi_damp[2] += spi_mosi

mcu['IO12'] += spi_miso
mcu['IO14'] += spi_cs_lcd
mcu['IO11'] += lcd_dc
mcu['IO17'] += lcd_rst

lcd['SCL'] += spi_sck
lcd['SDA'] += spi_mosi
lcd['CS'] += spi_cs_lcd
lcd['DC'] += lcd_dc
lcd['RES'] += lcd_rst
lcd['BLK'] += vcc_3v3

c_lcd_1[1] += vcc_3v3
c_lcd_1[2] += gnd
c_lcd_2[1] += vcc_3v3
c_lcd_2[2] += gnd

# ============================================================
# 8. MicroSD 卡座连接（SPI, 共享总线）
# ============================================================

sd_card['VCC'] += vcc_3v3
sd_card['GND'] += gnd

spi_cs_sd = Net('SPI_CS_SD')
sd_card['SCK'] += spi_sck
sd_card['MOSI'] += spi_mosi
sd_card['MISO'] += spi_miso
sd_card['CS'] += spi_cs_sd
mcu['IO10'] += spi_cs_sd

sd_card['SHIELD'] += gnd

# ============================================================
# 9. DFPlayer Mini 音频播放模块连接（UART + 双去耦）
# ============================================================

audio_player['VCC'] += vcc_3v3
audio_player['GND'] += gnd

uart_tx = Net('UART_TX')
uart_rx = Net('UART_RX')
dfplayer_busy = Net('DFPLAYER_BUSY')

mcu['IO18'] += uart_tx
mcu['IO19'] += uart_rx
mcu['IO20'] += dfplayer_busy

audio_player['RX'] += uart_tx
audio_player['TX'] += uart_rx
audio_player['BUSY'] += dfplayer_busy

audio_player['SPK1'] += speaker[1]
audio_player['SPK2'] += speaker[2]

# ★ DFPlayer双去耦 (10uF + 100nF)
c_audio_1[1] += vcc_3v3
c_audio_1[2] += gnd
c_audio_2[1] += vcc_3v3
c_audio_2[2] += gnd

# ============================================================
# 10. INMP441 麦克风连接（I2S + 阻尼电阻）
# ============================================================

microphone['VDD'] += vcc_3v3
microphone['GND'] += gnd

# ★ I2S信号通过阻尼电阻
i2s_sck = Net('I2S_SCK')
i2s_sd = Net('I2S_SD')
i2s_ws = Net('I2S_WS')

i2s_sck_mcu = Net('I2S_SCK_MCU')
i2s_ws_mcu = Net('I2S_WS_MCU')

mcu['IO7'] += i2s_sck_mcu
r_i2s_sck_damp[1] += i2s_sck_mcu
r_i2s_sck_damp[2] += i2s_sck

mcu['IO16'] += i2s_ws_mcu
r_i2s_ws_damp[1] += i2s_ws_mcu
r_i2s_ws_damp[2] += i2s_ws

mcu['IO15'] += i2s_sd    # I2S数据是输入，不需要阻尼

microphone['SCK'] += i2s_sck
microphone['SD'] += i2s_sd
microphone['WS'] += i2s_ws

microphone['L_R'] += gnd

c_mic[1] += vcc_3v3
c_mic[2] += gnd

# ============================================================
# 11. WS2812B RGB LED 连接（电平转换 + 独立去耦）
# ============================================================

# ★ 74AHCT125 电平转换器
level_shifter['VCC'] += vcc_5v_prot    # 5V供电
level_shifter['GND'] += gnd

# 使用通道1进行LED数据电平转换
# OE接地(始终使能), A接MCU(3.3V), Y接LED(5V)
level_shifter['1OE'] += gnd
level_shifter['2OE'] += gnd     # 备用通道也使能(可做扩展)
level_shifter['3OE'] += vcc_5v_prot  # 未使用通道禁用
level_shifter['4OE'] += vcc_5v_prot  # 未使用通道禁用

# LED数据路径: MCU IO21 → 串联100Ω → 74AHCT125 1A → 1Y → LED1 DIN
led_data_mcu = Net('LED_DATA_MCU')
led_data_buf = Net('LED_DATA_BUF')  # 电平转换后
led_data_out = Net('LED_DATA_5V')   # 到LED链

mcu['IO21'] += led_data_mcu
r_led_data_series[1] += led_data_mcu
r_led_data_series[2] += led_data_buf
level_shifter['1A'] += led_data_buf
level_shifter['1Y'] += led_data_out

# 备用通道输入拉低防止振荡
level_shifter['2A'] += gnd
level_shifter['3A'] += gnd
level_shifter['4A'] += gnd

# 电平转换器去耦
c_level_shifter[1] += vcc_5v_prot
c_level_shifter[2] += gnd

# LED连接 (使用保护后的5V)
led1['VDD'] += vcc_5v_prot
led1['GND'] += gnd
led2['VDD'] += vcc_5v_prot
led2['GND'] += gnd
led3['VDD'] += vcc_5v_prot
led3['GND'] += gnd

# LED数据链
led1['DIN'] += led_data_out
led1['DOUT'] += led2['DIN']
led2['DOUT'] += led3['DIN']

# ★ 每个LED独立100nF去耦电容 (靠近VDD-GND放置)
c_led1[1] += vcc_5v_prot
c_led1[2] += gnd
c_led2[1] += vcc_5v_prot
c_led2[2] += gnd
c_led3[1] += vcc_5v_prot
c_led3[2] += gnd

# ============================================================
# 12. 按键连接（含硬件去抖电容）
# ============================================================

# 按键1：模式选择（IO8）
key_mode_net = Net('KEY_MODE')
mcu['IO8'] += key_mode_net
key_mode_net += r_key_mode_pullup[1]
r_key_mode_pullup[2] += vcc_3v3
key_mode_net += key_mode[1]
key_mode[2] += gnd
# ★ 硬件去抖: 100nF 电容并联在按键两端
c_key_mode_debounce[1] += key_mode_net
c_key_mode_debounce[2] += gnd

# 按键2：手势选择（IO3）
key_select_net = Net('KEY_SELECT')
mcu['IO3'] += key_select_net
key_select_net += r_key_select_pullup[1]
r_key_select_pullup[2] += vcc_3v3
key_select_net += key_select[1]
key_select[2] += gnd
c_key_select_debounce[1] += key_select_net
c_key_select_debounce[2] += gnd

# 按键3：播放/确认（IO0）
key_play_net = Net('KEY_PLAY')
mcu['IO0'] += key_play_net
key_play_net += r_key_play_pullup[1]
r_key_play_pullup[2] += vcc_3v3
key_play_net += key_play[1]
key_play[2] += gnd
c_key_play_debounce[1] += key_play_net
c_key_play_debounce[2] += gnd

# ============================================================
# 13. 生成网表和验证
# ============================================================

if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    print("正在执行电气规则检查 (ERC)...")
    ERC()

    netlist_path = os.path.join(output_dir, 'cyberwand_netlist.net')
    print(f"\n正在生成网表文件...")
    generate_netlist(file_=netlist_path)
    print(f"网表已生成: {netlist_path}")

    print("\n电路统计信息 (v2.0):")
    print("- 主控芯片: ESP32-S3-WROOM-1N16R8")
    print("- 传感器: MPU6050 6轴运动传感器")
    print("- 显示屏: HS20S010B LCD (240x320, ST7789V2驱动)")
    print("- 存储: MicroSD卡座")
    print("- 音频: DFPlayer Mini + INMP441麦克风")
    print("- LED: WS2812B x3 (电平转换后)")
    print("- 电源: TP4056 + ME6211 + 603040锂电池 + 电源开关")
    print("- 接口: USB Type-C (含ESD+过流保护)")
    print("- 按键: 3个 (含硬件去抖)")
    print("- 充电指示: 红色LED + 绿色LED")
    print("\n★ v2.0 新增保护组件:")
    print("  - USBLC6-2SC6 USB ESD保护 (±30kV)")
    print("  - PTC自恢复保险丝 500mA (USB过流保护)")
    print("  - SN74AHCT125 电平转换 (3.3V→5V)")
    print("  - SPDT滑动电源开关")
    print("  - SPI/I2S 33Ω阻尼电阻")
    print("  - USB 22Ω串联电阻")
    print("  - 按键100nF去抖电容")
    print("  - 每个WS2812B独立100nF去耦")
    print("\n电路连接描述完成！")
