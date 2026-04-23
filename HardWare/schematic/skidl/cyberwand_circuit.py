"""
赛博魔杖 (CyberWand) 完整电路连接描述 v3.0 - 极简版
使用 SKiDL 描述所有硬件连接

v3.0 变更 (极简版):
    - 需求精简: 仅保留"手势识别 + 蓝牙数据发送/广播"核心功能
    - 移除 LCD 模块 (HS20S010B TFT)
    - 移除 MicroSD 卡座 (本地存储由 ESP32 内部 Flash 承担)
    - 移除 DFPlayer Mini 与扬声器 (取消音频输出)
    - 移除 INMP441 麦克风 (取消语音检测)
    - 移除 WS2812B 可编程 RGB LED + SN74AHCT125 电平转换
        (用 ESP32 片内 GPIO 直驱的普通 LED 做状态指示)
    - 串口/烧录仍复用 USB Type-C (ESP32-S3 原生 USB)

v2.3 继承 (保留电气属性修复):
    ★ ME6211 SOT-23 Pin2/Pin3 按数据手册接线: Pin1=VIN, Pin2=VOUT, Pin3=VSS
    ★ TP4056 TEMP 接 GND 禁用温度监测
    ★ ESP32 EN RC 复位 (10K 上拉 + 1uF 到 GND)
    ★ TP4056 BAT 端 10uF 去耦
    ★ MPU6050 数据手册强制要求: CPOUT=2.2nF, REGOUT=100nF, CLKIN/FSYNC=GND

保留硬件清单:
    - ESP32-S3-WROOM-1 (主控, 含 BLE 5.0)
    - MPU6050 (6 轴 IMU, I2C)
    - USB Type-C (充电 + 烧录/调试)
    - TP4056 (锂电池充电管理)
    - ME6211 (3.3V LDO)
    - 603040 锂电池 (800mAh)
    - USBLC6-2SC6 (USB ESD 保护)
    - PTC 500mA 自恢复保险丝
    - 电源开关
    - 2 颗充电状态指示 LED (红/绿, 受 TP4056 CHRG/STDBY 驱动)
    - 1 颗系统状态 LED (受 ESP32 GPIO 直接驱动, 用于手势识别反馈)
    - 1 个用户按键 (单键通过单击/双击/长按实现多功能)
"""

from skidl import Net, generate_netlist, ERC

from esp32_s3_wroom import ESP32_S3_WROOM
from mpu6050_part import MPU6050
from tp4056_part import TP4056
from me6211_part import ME6211
from usb_type_c_part import USB_TYPE_C
from battery_603040 import BATTERY_603040
from led_part import LED_RED, LED_GREEN
from usblc6_2sc6_part import USBLC6_2SC6
from ptc_fuse_part import PTC_FUSE_500MA
from power_switch_part import POWER_SWITCH
from passive_parts import (R_10K, R_4K7, R_2K, R_5K1, R_1K,
                           R_100, R_22,
                           C_2N2, C_100N, C_10U, C_1U, C_22U,
                           SWITCH)
import os


# ============================================================
# 1. 元器件实例
# ============================================================

mcu = ESP32_S3_WROOM()
imu = MPU6050()

usb_conn = USB_TYPE_C()
battery = BATTERY_603040()
charger = TP4056()
ldo = ME6211()

usb_esd = USBLC6_2SC6()
ptc_fuse = PTC_FUSE_500MA()
pwr_switch = POWER_SWITCH()

# 交互元件
key_user = SWITCH()                # 单键多功能 (单击/双击/长按)
led_status = LED_GREEN()            # 系统状态指示 (绿色, GPIO 直驱)
led_charging = LED_RED()            # 充电中 (红色, TP4056 CHRG)
led_charged = LED_GREEN()           # 充满 (绿色, TP4056 STDBY)

# --- 电阻 ---
r_en_pullup = R_10K()
r_i2c_sda_pullup = R_4K7()
r_i2c_scl_pullup = R_4K7()
r_key_user_pullup = R_10K()
r_io46_pulldown = R_10K()
r_cc1 = R_5K1()
r_cc2 = R_5K1()
r_prog = R_2K()
r_led_status = R_1K()               # 状态 LED 限流
r_led_charging = R_1K()
r_led_charged = R_1K()
r_usb_dp = R_22()
r_usb_dn = R_22()

# --- 电容 ---
c_mcu_1 = C_100N()
c_mcu_2 = C_100N()
c_mcu_3 = C_10U()
c_en_reset = C_1U()                 # ESP32 EN 上电复位延迟
c_imu = C_100N()                    # MPU6050 VDD 去耦
c_imu_vlogic = C_100N()             # MPU6050 VLOGIC 去耦
c_imu_cpout = C_2N2()               # MPU6050 CPOUT 电荷泵 2.2nF
c_imu_regout = C_100N()             # MPU6050 REGOUT 内部稳压 100nF
c_ldo_in = C_10U()
c_ldo_out = C_10U()
c_usb = C_10U()
c_vbus_bulk = C_22U()
c_bat = C_10U()                     # TP4056 BAT 端去耦
c_key_user_debounce = C_100N()


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
# 3. USB Type-C (ESD + 过流保护)
# ============================================================

usb_conn['VBUS1'] += vcc_5v         # Pin2: VBUS
usb_conn['VBUS2'] += vcc_5v         # Pin11: VBUS

ptc_fuse[1] += vcc_5v
ptc_fuse[2] += vcc_5v_prot

usb_conn['GND1'] += gnd             # Pin1: GND
usb_conn['GND2'] += gnd             # Pin12: GND
usb_conn['SHELL1'] += gnd           # Pin13: SHELL
usb_conn['SHELL2'] += gnd           # Pin14: SHELL

# CC 配置通道
usb_conn['CC1'] += r_cc1[1]
r_cc1[2] += gnd
usb_conn['CC2'] += r_cc2[1]
r_cc2[2] += gnd

usb_esd['VBUS'] += vcc_5v_prot
usb_esd['GND'] += gnd

usb_d_plus = Net('USB_DP')
usb_d_minus = Net('USB_DN')
usb_dp_int = Net('USB_DP_INT')
usb_dn_int = Net('USB_DN_INT')

usb_conn['DP1'] += usb_d_plus
usb_conn['DP2'] += usb_d_plus
usb_conn['DN1'] += usb_d_minus
usb_conn['DN2'] += usb_d_minus

r_usb_dp[1] += usb_d_plus
r_usb_dp[2] += usb_dp_int
usb_esd['IO1_1'] += usb_dp_int
usb_esd['IO1_2'] += usb_dp_int

r_usb_dn[1] += usb_d_minus
r_usb_dn[2] += usb_dn_int
usb_esd['IO2_1'] += usb_dn_int
usb_esd['IO2_2'] += usb_dn_int

mcu['IO19'] += usb_dn_int           # ESP32 原生 USB D-
mcu['IO20'] += usb_dp_int           # ESP32 原生 USB D+

c_usb[1] += vcc_5v_prot
c_usb[2] += gnd
c_vbus_bulk[1] += vcc_5v_prot
c_vbus_bulk[2] += gnd


# ============================================================
# 4. TP4056 充电管理
# ============================================================

charger['VCC'] += vcc_5v_prot       # Pin4
charger['GND'] += gnd               # Pin3
charger['BAT'] += vcc_bat           # Pin5
charger['CE'] += vcc_5v_prot        # Pin8
charger['TEMP'] += gnd              # Pin1: 接 GND 禁用温度监测
charger['EP'] += gnd                # Pin9: EP 散热焊盘

charger['PROG'] += r_prog[1]        # Pin2: ICHG = 1000/RPROG = 500mA
r_prog[2] += gnd

c_bat[1] += vcc_bat
c_bat[2] += gnd

# CHRG/STDBY LED (开漏: VCC → R → LED → 引脚)
chrg_net = Net('CHRG_STATUS')
charger['CHRG'] += chrg_net
r_led_charging[1] += vcc_5v_prot
r_led_charging[2] += led_charging['A']
led_charging['K'] += chrg_net

stdby_net = Net('STDBY_STATUS')
charger['STDBY'] += stdby_net
r_led_charged[1] += vcc_5v_prot
r_led_charged[2] += led_charged['A']
led_charged['K'] += stdby_net

# 电池
battery['+'] += vcc_bat
battery['-'] += gnd

# 电源开关 (NC 悬空)
pwr_switch['COM'] += vcc_bat
pwr_switch['NO'] += vcc_bat_sw

# ME6211 LDO
ldo['VIN'] += vcc_bat_sw            # Pin1
ldo['VOUT'] += vcc_3v3              # Pin2
ldo['VSS'] += gnd                   # Pin3

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

# EN 引脚 RC 复位 (10K 上拉 + 1uF 到 GND)
mcu['EN'] += r_en_pullup[1]
r_en_pullup[2] += vcc_3v3
c_en_reset[1] += r_en_pullup[1]
c_en_reset[2] += gnd

mcu['IO46'] += r_io46_pulldown[1]
r_io46_pulldown[2] += gnd

c_mcu_1[1] += vcc_3v3
c_mcu_1[2] += gnd
c_mcu_2[1] += vcc_3v3
c_mcu_2[2] += gnd
c_mcu_3[1] += vcc_3v3
c_mcu_3[2] += gnd


# ============================================================
# 6. MPU6050 (I2C)
# ============================================================

imu['VDD'] += vcc_3v3               # Pin13: 主电源
imu['VLOGIC'] += vcc_3v3            # Pin8: 数字 I/O 参考电压
imu['GND'] += gnd                   # Pin18: 地

# I2C
i2c_sda = Net('I2C_SDA')
i2c_scl = Net('I2C_SCL')

mcu['IO4'] += i2c_sda
mcu['IO5'] += i2c_scl
imu['SDA'] += i2c_sda               # Pin24
imu['SCL'] += i2c_scl               # Pin23

r_i2c_sda_pullup[1] += i2c_sda
r_i2c_sda_pullup[2] += vcc_3v3
r_i2c_scl_pullup[1] += i2c_scl
r_i2c_scl_pullup[2] += vcc_3v3

imu['AD0'] += gnd                   # Pin9: 地址 = 0x68

mpu_int = Net('MPU6050_INT')
imu['INT'] += mpu_int               # Pin12
mcu['IO6'] += mpu_int

# 数据手册强制要求的引脚连接
imu['CLKIN'] += gnd                 # Pin1: 不用外部时钟
imu['FSYNC'] += gnd                 # Pin11: 不用帧同步

# 数据手册强制要求的外部电容
c_imu[1] += vcc_3v3
c_imu[2] += gnd

c_imu_vlogic[1] += imu['VLOGIC']
c_imu_vlogic[2] += gnd

c_imu_cpout[1] += imu['CPOUT']      # Pin20: 电荷泵 2.2nF
c_imu_cpout[2] += gnd

c_imu_regout[1] += imu['REGOUT']    # Pin10: 内部稳压 100nF
c_imu_regout[2] += gnd


# ============================================================
# 7. 串口调试：复用 USB Type-C
# ============================================================
# ESP32-S3 内置 USB Serial/JTAG, 固件 Serial 通过 USB CDC 输出
# 无需外接 USB 转 TTL


# ============================================================
# 8. 系统状态 LED (GPIO 直驱)
# ============================================================
# 用 ESP32 GPIO 直接驱动普通 LED 做状态指示
# 手势识别反馈、充电/检测模式区分

led_status_net = Net('LED_STATUS')
mcu['IO21'] += led_status_net
r_led_status[1] += led_status_net
r_led_status[2] += led_status['A']
led_status['K'] += gnd


# ============================================================
# 9. 用户按键 (单键多功能)
# ============================================================
# 单击/双击/长按实现模式切换、录制、唤醒

key_user_net = Net('KEY_USER')
mcu['IO8'] += key_user_net
key_user_net += r_key_user_pullup[1]
r_key_user_pullup[2] += vcc_3v3
key_user_net += key_user[1]
key_user[2] += gnd
c_key_user_debounce[1] += key_user_net
c_key_user_debounce[2] += gnd


# ============================================================
# 10. 生成网表
# ============================================================

if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    print("执行 ERC...")
    ERC()

    netlist_path = os.path.join(output_dir, 'cyberwand_netlist.net')
    print("\n生成网表...")
    generate_netlist(file_=netlist_path)
    print(f"网表已生成: {netlist_path}")
    print("\nv3.0 极简版电路设计完成! (仅保留手势识别 + 蓝牙核心)")
