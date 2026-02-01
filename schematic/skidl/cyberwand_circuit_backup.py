"""
赛博魔杖 (CyberWand) 完整电路连接描述
使用 SKiDL 描述所有硬件连接
"""

from skidl import Net, generate_netlist, ERC

# 导入所有元器件模板
from esp32_s3_wroom import ESP32_S3_WROOM
from mpu6050_part import MPU6050
from st7789_lcd_part import ST7789_LCD
from microsd_socket_part import MICROSD_SOCKET
from dfplayer_mini_part import DFPLAYER_MINI
from inmp441_part import INMP441
from ws2812b_part import WS2812B
from tp4056_part import TP4056
from me6211_part import ME6211
from usb_type_c_part import USB_TYPE_C
from battery_603040 import BATTERY_603040
from led_part import LED_RED, LED_GREEN
from passive_parts import R_10K, R_4K7, R_2K, R_5K1, R_1K, C_100N, C_10U, SWITCH, SPEAKER
import os

# ============================================================
# 1. 创建所有元器件实例
# ============================================================

# 主控芯片
mcu = ESP32_S3_WROOM()

# 传感器和外设
imu = MPU6050()  # 6轴运动传感器
lcd = ST7789_LCD()  # 1.8寸 TFT LCD显示屏
sd_card = MICROSD_SOCKET()  # MicroSD卡座
audio_player = DFPLAYER_MINI()  # 音频播放模块
microphone = INMP441()  # MEMS麦克风
led1 = WS2812B()  # RGB LED 1
led2 = WS2812B()  # RGB LED 2 (可选)
led3 = WS2812B()  # RGB LED 3 (可选)

# 电源管理
usb_conn = USB_TYPE_C()  # Type-C接口
battery = BATTERY_603040()  # 锂电池
charger = TP4056()  # 充电管理芯片
ldo = ME6211()  # LDO稳压芯片

# 按键
key_mode = SWITCH()  # 模式选择按键
key_select = SWITCH()  # 手势选择按键
key_play = SWITCH()  # 播放/确认按键

# 扬声器
speaker = SPEAKER()

# 充电指示灯
led_charging = LED_RED()    # 红色LED - 充电中
led_charged = LED_GREEN()   # 绿色LED - 充满

# 被动元器件
# 上拉电阻
r_en_pullup = R_10K()  # ESP32 EN引脚上拉
r_i2c_sda_pullup = R_4K7()  # I2C SDA上拉
r_i2c_scl_pullup = R_4K7()  # I2C SCL上拉
r_key_mode_pullup = R_10K()  # 按键1上拉
r_key_select_pullup = R_10K()  # 按键2上拉
r_key_play_pullup = R_10K()  # 按键3上拉

# Type-C CC配置电阻
r_cc1 = R_5K1()  # CC1下拉电阻
r_cc2 = R_5K1()  # CC2下拉电阻

# TP4056充电电流设置电阻
r_prog = R_2K()  # 设置充电电流500mA

# LED 限流电阻
r_led_red = R_1K()    # 红色LED限流电阻
r_led_green = R_1K()  # 绿色LED限流电阻

# 去耦电容
c_mcu_1 = C_100N()  # ESP32去耦1
c_mcu_2 = C_100N()  # ESP32去耦2
c_mcu_3 = C_10U()  # ESP32去耦3
c_imu = C_100N()  # MPU6050去耦
c_lcd_1 = C_100N()  # LCD去耦1
c_lcd_2 = C_10U()  # LCD去耦2
c_audio = C_10U()  # DFPlayer去耦
c_mic = C_100N()  # INMP441去耦
c_led = C_100N()  # WS2812B去耦
c_ldo_in = C_10U()  # ME6211输入电容
c_ldo_out = C_10U()  # ME6211输出电容
c_usb = C_10U()  # USB滤波电容

# ============================================================
# 2. 创建电源网络
# ============================================================

# 创建电源网络
vcc_5v = Net('5V')  # 5V电源网络
vcc_3v3 = Net('3V3')  # 3.3V电源网络
vcc_bat = Net('BAT')  # 电池电压网络
gnd = Net('GND')  # 地网络

# ============================================================
# 3. USB Type-C 接口连接
# ============================================================

# Type-C VBUS连接到充电芯片
usb_conn['VBUS_A4'] += vcc_5v
usb_conn['VBUS_B4'] += vcc_5v

# Type-C GND连接
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

# Type-C USB数据线连接到ESP32（需要ESD保护，此处简化）
# 注意：实际设计中应添加ESD保护二极管
usb_d_plus = Net('USB_DP')
usb_d_minus = Net('USB_DN')
usb_conn['DP1'] += usb_d_plus
usb_conn['DP2'] += usb_d_plus
usb_conn['DN1'] += usb_d_minus
usb_conn['DN2'] += usb_d_minus

# USB滤波电容
c_usb[1] += vcc_5v
c_usb[2] += gnd

# ============================================================
# 4. 电源管理电路连接
# ============================================================

# TP4056 充电管理芯片连接
charger['VIN'] += vcc_5v
charger['GND'] += gnd
charger['BAT'] += vcc_bat
charger['CE'] += vcc_3v3  # 充电使能，接高电平
charger['RST'] += vcc_3v3  # 复位，接高电平

# TP4056 充电电流设置（2K电阻，500mA充电电流）
charger['PROG'] += r_prog[1]
r_prog[2] += gnd

# TP4056 状态指示（预留LED连接）
# charger['CHRG']  # 充电状态指示
# charger['STDBY']  # 待机状态指示

# TP4056 充电指示灯连接
# CHRG 引脚 - 充电时为低电平，连接红色LED
charger['CHRG'] += r_led_red[1]
r_led_red[2] += led_charging['A']
led_charging['K'] += gnd

# STDBY 引脚 - 充满时为低电平，连接绿色LED
charger['STDBY'] += r_led_green[1]
r_led_green[2] += led_charged['A']
led_charged['K'] += gnd

# 锂电池连接
battery['+'] += vcc_bat
battery['-'] += gnd

# ME6211 LDO稳压芯片连接
ldo['VIN'] += vcc_bat
ldo['GND'] += gnd
ldo['VOUT'] += vcc_3v3

# LDO去耦电容
c_ldo_in[1] += vcc_bat
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
mcu['GND3'] += gnd
mcu['GND4'] += gnd
mcu['GND5'] += gnd
mcu['GND2'] += gnd
mcu['GND3'] += gnd
mcu['GND4'] += gnd

# EN引脚上拉
mcu['EN'] += r_en_pullup[1]
r_en_pullup[2] += vcc_3v3

# ESP32去耦电容
c_mcu_1[1] += vcc_3v3
c_mcu_1[2] += gnd
c_mcu_2[1] += vcc_3v3
c_mcu_2[2] += gnd
c_mcu_3[1] += vcc_3v3
c_mcu_3[2] += gnd

# ============================================================
# 6. MPU6050 陀螺仪传感器连接（I2C）
# ============================================================

# 电源连接
imu['VCC'] += vcc_3v3
imu['GND'] += gnd
imu['VLOGIC'] += vcc_3v3

# I2C总线连接
i2c_sda = Net('I2C_SDA')
i2c_scl = Net('I2C_SCL')

mcu['IO33'] += i2c_sda
mcu['IO25'] += i2c_scl
imu['SDA'] += i2c_sda
imu['SCL'] += i2c_scl

# I2C上拉电阻
r_i2c_sda_pullup[1] += i2c_sda
r_i2c_sda_pullup[2] += vcc_3v3
r_i2c_scl_pullup[1] += i2c_scl
r_i2c_scl_pullup[2] += vcc_3v3

# I2C地址选择（AD0接地，地址为0x68）
imu['AD0'] += gnd

# 中断引脚（可选）
mpu_int = Net('MPU6050_INT')
imu['INT'] += mpu_int
mcu['IO26'] += mpu_int

# MPU6050去耦电容
c_imu[1] += vcc_3v3
c_imu[2] += gnd

# ============================================================
# 7. ST7789 LCD 显示屏连接（SPI）
# ============================================================

# 电源连接
lcd['VCC'] += vcc_3v3
lcd['GND'] += gnd

# SPI总线连接（与SD卡共享）
spi_sck = Net('SPI_SCK')
spi_mosi = Net('SPI_MOSI')
spi_miso = Net('SPI_MISO')
spi_cs_lcd = Net('SPI_CS_LCD')
lcd_dc = Net('LCD_DC')
lcd_rst = Net('LCD_RST')

mcu['SHD_SD2'] += spi_sck  # GPIO9
mcu['IO13'] += spi_mosi  # GPIO13
mcu['IO12'] += spi_miso  # GPIO12
mcu['IO15'] += spi_cs_lcd  # GPIO15
mcu['IO14'] += lcd_dc  # GPIO14
mcu['IO16'] += lcd_rst  # GPIO16

lcd['SCK'] += spi_sck
lcd['MOSI'] += spi_mosi
# LCD不需要MISO，已删除此引脚
lcd['CS'] += spi_cs_lcd
lcd['DC'] += lcd_dc
lcd['RST'] += lcd_rst

# LCD背光常亮
lcd['BL'] += vcc_3v3

# LCD去耦电容
c_lcd_1[1] += vcc_3v3
c_lcd_1[2] += gnd
c_lcd_2[1] += vcc_3v3
c_lcd_2[2] += gnd

# ============================================================
# 8. MicroSD 卡座连接（SPI）
# ============================================================

# 电源连接
sd_card['VCC'] += vcc_3v3
sd_card['GND'] += gnd

# SPI总线连接（与LCD共享）
spi_cs_sd = Net('SPI_CS_SD')

sd_card['SCK'] += spi_sck
sd_card['MOSI'] += spi_mosi
sd_card['MISO'] += spi_miso
sd_card['CS'] += spi_cs_sd
mcu['SVN_SD3'] += spi_cs_sd  # GPIO10

# 屏蔽接地
sd_card['SHIELD'] += gnd

# ============================================================
# 9. DFPlayer Mini 音频播放模块连接（UART）
# ============================================================

# 电源连接
audio_player['VCC'] += vcc_3v3
audio_player['GND'] += gnd

# UART连接（交叉连接）
uart_tx = Net('UART_TX')
uart_rx = Net('UART_RX')
dfplayer_busy = Net('DFPLAYER_BUSY')

mcu['IO18'] += uart_tx  # ESP32 TX -> DFPlayer RX
mcu['IO17'] += uart_rx  # ESP32 RX <- DFPlayer TX
mcu['IO19'] += dfplayer_busy

audio_player['RX'] += uart_tx
audio_player['TX'] += uart_rx
audio_player['BUSY'] += dfplayer_busy

# 扬声器连接
audio_player['SPK1'] += speaker[1]
audio_player['SPK2'] += speaker[2]

# DFPlayer去耦电容
c_audio[1] += vcc_3v3
c_audio[2] += gnd

# ============================================================
# 10. INMP441 麦克风连接（I2S）
# ============================================================

# 电源连接
microphone['VDD'] += vcc_3v3
microphone['GND'] += gnd

# I2S总线连接
i2s_sck = Net('I2S_SCK')
i2s_sd = Net('I2S_SD')
i2s_ws = Net('I2S_WS')

mcu['IO34'] += i2s_sck  # GPIO34
mcu['IO35'] += i2s_sd  # GPIO35
mcu['IO32'] += i2s_ws  # GPIO32

microphone['SCK'] += i2s_sck
microphone['SD'] += i2s_sd
microphone['WS'] += i2s_ws

# 声道选择（接地选择左声道）
microphone['L_R'] += gnd

# 麦克风去耦电容
c_mic[1] += vcc_3v3
c_mic[2] += gnd

# ============================================================
# 11. WS2812B RGB LED 连接（串联）
# ============================================================

# LED电源（使用5V以获得更好的亮度）
led1['VDD'] += vcc_5v
led1['GND'] += gnd
led2['VDD'] += vcc_5v
led2['GND'] += gnd
led3['VDD'] += vcc_5v
led3['GND'] += gnd

# LED数据线串联
led_data = Net('LED_DATA')

mcu['IO21'] += led_data  # GPIO21
led1['DIN'] += led_data
led1['DOUT'] += led2['DIN']  # LED1输出连接LED2输入
led2['DOUT'] += led3['DIN']  # LED2输出连接LED3输入

# LED去耦电容
c_led[1] += vcc_5v
c_led[2] += gnd

# ============================================================
# 12. 按键连接
# ============================================================

# 按键1：模式选择（IO4）
key_mode_net = Net('KEY_MODE')
mcu['IO4'] += key_mode_net
key_mode_net += r_key_mode_pullup[1]
r_key_mode_pullup[2] += vcc_3v3
key_mode_net += key_mode[1]
key_mode[2] += gnd

# 按键2：手势选择（IO5）
key_select_net = Net('KEY_SELECT')
mcu['IO5'] += key_select_net
key_select_net += r_key_select_pullup[1]
r_key_select_pullup[2] += vcc_3v3
key_select_net += key_select[1]
key_select[2] += gnd

# 按键3：播放/确认（IO0）- 使用IO0作为播放按键
# IO0在ESP32-S3上也是BOOT按键，按下时为低电平
key_play_net = Net('KEY_PLAY')
mcu['IO0'] += key_play_net  # GPIO0 - 也是BOOT按键
key_play_net += r_key_play_pullup[1]
r_key_play_pullup[2] += vcc_3v3
key_play_net += key_play[1]
key_play[2] += gnd

# ============================================================
# 13. 生成网表和验证
# ============================================================

if __name__ == '__main__':
    # 确保 output 目录存在
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 执行电气规则检查
    print("正在执行电气规则检查 (ERC)...")
    ERC()
    
    # 生成网表文件到 output 目录
    netlist_path = os.path.join(output_dir, 'cyberwand_netlist.net')
    print(f"\n正在生成网表文件...")
    generate_netlist(file_=netlist_path)
    print(f"网表已生成: {netlist_path}")
    
    # 打印统计信息
    print("\n电路统计信息:")
    print("- 主控芯片: ESP32-S3-WROOM-1N16R8")
    print("- 传感器: MPU6050 6轴运动传感器")
    print("- 显示屏: ST7789 LCD (128x160)")
    print("- 存储: MicroSD卡座")
    print("- 音频: DFPlayer Mini + INMP441麦克风")
    print("- LED: WS2812B x3 (串联) + 充电指示LED x2")
    print("- 电源: TP4056 + ME6211 + 603040锂电池")
    print("- 接口: USB Type-C")
    print("- 按键: 3个 (模式/选择/播放)")
    print("- 充电指示: 红色LED(充电中) + 绿色LED(充满)")
    print("\n电路连接描述完成！")
