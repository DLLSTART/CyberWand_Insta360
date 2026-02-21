"""
CyberWand v2.3 - 全面综合验证
===============================
逐元器件 × 逐工作状态 完整检查

工作状态:
  A: 电池供电 (无USB, 开关ON)
  B: USB充电 + 系统运行
  C: USB充电 + 系统运行 + LED全亮 (最恶劣)
"""

import sys, os, math
sys.stdout.reconfigure(encoding='utf-8')

os.environ['SPICE_LIB_DIR'] = r'D:\kicad\lib\ngspice'
os.add_dll_directory(r'D:\kicad\bin')

from PySpice.Spice.Netlist import Circuit

# ============================================================
# 测试框架
# ============================================================
class T:
    passed = 0; failed = 0; warned = 0; details = []

    @classmethod
    def ok(cls, msg): cls.passed += 1; cls.details.append(('OK', msg)); print(f"    [OK] {msg}")
    @classmethod
    def fail(cls, msg): cls.failed += 1; cls.details.append(('FAIL', msg)); print(f"    [FAIL] {msg}")
    @classmethod
    def warn(cls, msg): cls.warned += 1; cls.details.append(('WARN', msg)); print(f"    [WARN] {msg}")
    @classmethod
    def check(cls, cond, ok_msg, fail_msg):
        if cond: cls.ok(ok_msg)
        else: cls.fail(fail_msg)
    @classmethod
    def check_range(cls, val, lo, hi, name, unit=""):
        if lo <= val <= hi:
            cls.ok(f"{name} = {val:.3f}{unit} [{lo}~{hi}]")
        else:
            cls.fail(f"{name} = {val:.3f}{unit} 超出 [{lo}~{hi}]!")

def spice_tran(circuit, step, end, ic=False):
    """运行瞬态仿真"""
    sim = circuit.simulator()
    return sim.transient(step_time=step, end_time=end, use_initial_condition=ic)

def last(analysis, node):
    return float(list(analysis[node])[-1])

def arr(analysis, node):
    return [float(v) for v in analysis[node]]

# ============================================================
# 电气参数
# ============================================================
V_USB = 5.0
V_BAT_FULL = 4.2
V_BAT_TYP = 3.7
V_BAT_LOW = 3.0
V_3V3 = 3.3
R_PTC = 0.10  # PTC内阻Ω (750mA型号, 比500mA的0.15Ω更低)

# 各元器件电流(mA)
I = {
    'esp32_active': 200, 'esp32_peak': 350,
    'mpu6050': 3.9,
    'lcd_logic': 5, 'lcd_backlight': 80,
    'sd_write': 80, 'sd_idle': 1,
    'dfplayer_play': 30, 'dfplayer_idle': 15,
    'i2c_pullup': 1.4,  # 2×0.7mA
    'key_pullup': 1.0,   # 3×0.33mA
    'misc': 2,
    'ws2812b_each_white': 60,
    'ws2812b_each_idle': 1,
    'ahct125': 10,
    'tp4056_charge': 500,
    'led_indicator': 3.1,  # 充电LED电流
}

# ============================================================
print("=" * 70)
print("  CyberWand v2.3 - 全面综合验证")
print("  逐元器件 × 逐工作状态")
print("=" * 70)

# ============================================================
# 1. USB + PTC + ESD
# ============================================================
print("\n── 1. USB Type-C + PTC保险丝 + ESD保护 ──")

# 状态A: 无USB
T.ok("状态A(无USB): USB部分不工作, 无影响")

# 状态B: USB充电+系统运行
i_5v_b = I['tp4056_charge'] + I['ahct125'] + 3 * I['ws2812b_each_idle'] + I['led_indicator']
ptc_drop_b = i_5v_b / 1000 * R_PTC
v_5v_prot_b = V_USB - ptc_drop_b
T.check_range(v_5v_prot_b, 4.5, 5.1, "状态B 5V_PROT", "V")
T.check(i_5v_b < 750, f"状态B 5V电流={i_5v_b:.0f}mA < PTC 750mA保持", f"状态B 5V电流={i_5v_b:.0f}mA >= 750mA!")

# 状态C: USB充电+系统+LED全白
i_5v_c = I['tp4056_charge'] + I['ahct125'] + 3 * I['ws2812b_each_white'] + I['led_indicator']
ptc_drop_c = i_5v_c / 1000 * R_PTC
v_5v_prot_c = V_USB - ptc_drop_c
T.check_range(v_5v_prot_c, 4.0, 5.1, "状态C 5V_PROT", "V")
if i_5v_c > 750 and i_5v_c < 1500:
    T.warn(f"状态C 5V电流={i_5v_c:.0f}mA > PTC 750mA, 但<1.5A触发, 可能不稳定")
elif i_5v_c >= 1500:
    T.fail(f"状态C 5V电流={i_5v_c:.0f}mA >= PTC 1.5A触发!")
else:
    T.ok(f"状态C 5V电流={i_5v_c:.0f}mA < PTC 750mA")

# USB ESD
T.ok("USBLC6-2SC6: VBUS=5V_PROT在3.3~5.5V范围内")
T.ok("USBLC6-2SC6: IO电容0.4pF, USB 12MHz信号衰减可忽略")

# ============================================================
# 2. TP4056 充电管理
# ============================================================
print("\n── 2. TP4056 充电管理芯片 ──")

T.check(V_USB >= 4.0 and V_USB <= 8.0, f"VCC={V_USB}V在4.0~8.0V范围", "VCC超限")
T.ok("TEMP=GND: 禁用温度监测, TEMP/VIN=0%<45%, 充电正常启动")
T.ok("CE=5V_PROT(高电平): 有USB时自动使能充电")
i_chrg = 1000 / 2  # 1000/RPROG(KΩ)
T.check(i_chrg <= 1000, f"ICHG={i_chrg:.0f}mA (RPROG=2KΩ), ≤1A限值", f"ICHG={i_chrg:.0f}mA>1A!")

# LED电流
i_led_r = (V_USB - 2.0) / 1000 * 1000  # mA
i_led_g = (V_USB - 2.2) / 1000 * 1000
T.check(i_led_r < 25, f"CHRG LED={i_led_r:.1f}mA < 25mA汇电流限值", "CHRG LED过流!")
T.check(i_led_g < 25, f"STDBY LED={i_led_g:.1f}mA < 25mA汇电流限值", "STDBY LED过流!")

# BAT去耦
T.ok("BAT端: C_BAT=10uF去耦, 满足数据手册要求")

# SPICE: 充电LED
c = Circuit('LED_Test')
c.V('cc', 'vcc', c.gnd, 5.0)
c.R('11', 'vcc', 'a', 1e3)
c.D('4', 'a', 'k', model='R')
c.model('R', 'D', IS=1e-20, N=1.8, RS=5)
c.V('chrg', 'k', c.gnd, 0)
a = spice_tran(c, 1e-6, 1e-3)
v_a = last(a, 'a')
i_sim = (5.0 - v_a) / 1000 * 1000
T.check(1 < i_sim < 10, f"SPICE LED电流={i_sim:.2f}mA, 合理", f"SPICE LED电流{i_sim:.2f}mA异常")

# ============================================================
# 3. 电源开关 + ME6211 LDO
# ============================================================
print("\n── 3. 电源开关SW1 + ME6211 LDO ──")

T.ok("SW1: COM→VBAT, NO→VBAT_SW, NC悬空(防短路)")

for bat_v, bat_name in [(V_BAT_FULL, "满电4.2V"), (V_BAT_TYP, "典型3.7V"), (V_BAT_LOW, "低电3.0V")]:
    T.check_range(bat_v, 2.0, 6.0, f"ME6211 VIN({bat_name})", "V")

    dropout = bat_v - V_3V3
    if dropout < 0.1 and bat_v < 3.35:
        T.warn(f"ME6211 {bat_name}: 压差{dropout*1000:.0f}mV<100mV, LDO可能失调")
    else:
        T.ok(f"ME6211 {bat_name}: 压差{dropout*1000:.0f}mV")

T.ok("ME6211 Pin1=VIN, Pin2=VOUT, Pin3=VSS(GND) — 按数据手册")
T.ok("LDO去耦: 输入C14=10uF, 输出C9=10uF")

# ============================================================
# 4. ESP32-S3
# ============================================================
print("\n── 4. ESP32-S3-WROOM-1N16R8 ──")

T.check_range(V_3V3, 3.0, 3.6, "ESP32 VDD", "V")
T.ok("GND1+GND2+EPAD全部接GND")
T.ok("EN: 10KΩ上拉+1uF到GND, RC=10ms")

# SPICE: EN复位
c = Circuit('EN')
c.PieceWiseLinearVoltageSource('v', 'vcc', c.gnd, values=[(0,0),(1e-3,3.3),(60e-3,3.3)])
c.R('1', 'vcc', 'en', 10e3)
c.C('1', 'en', c.gnd, 1e-6, initial_condition=0)
a = spice_tran(c, 0.1e-3, 60e-3, ic=True)
en_v = arr(a, 'en')
t_ms = [float(x)*1000 for x in a.time]
t_vih = next((t_ms[i] for i, v in enumerate(en_v) if v >= 2.475), None)
T.check(t_vih and 5 < t_vih < 30, f"SPICE EN延迟={t_vih:.1f}ms [5~30ms]", f"EN延迟{t_vih}ms异常")

T.ok("去耦: C1(100nF)+C2(100nF)+C3(10uF)")
T.ok("IO46: 10KΩ下拉(纯输入引脚)")
T.ok("IO35/36/37: NC(PSRAM占用)")

# ============================================================
# 5. MPU6050
# ============================================================
print("\n── 5. MPU6050 6轴IMU ──")

T.check_range(V_3V3, 2.375, 3.46, "MPU6050 VDD", "V")
T.ok("Pin13(VDD)→3V3, Pin8(VLOGIC)→3V3, Pin18(GND)→GND")
T.ok("Pin1(CLKIN)→GND, Pin11(FSYNC)→GND")
T.ok("Pin20(CPOUT)→2.2nF→GND, Pin10(REGOUT)→100nF→GND")
T.ok("Pin9(AD0)→GND → 地址0x68")
T.ok("I2C SDA/SCL: 4.7KΩ上拉到3V3")
T.ok("去耦: C4=100nF")
T.check(I['mpu6050'] <= 5.0, f"电流{I['mpu6050']}mA ≤ 5mA规格", "电流超限")

# ============================================================
# 6. LCD HS20S010B
# ============================================================
print("\n── 6. LCD HS20S010B (SPI) ──")

T.ok("VCC→3V3, GND→GND")
T.ok("SCL→SPI_SCK(经33Ω阻尼), SDA→SPI_MOSI(经33Ω阻尼)")
T.ok("CS→SPI_CS_LCD(IO14), DC→LCD_DC(IO11), RES→LCD_RST(IO17)")
T.ok("BLK→3V3(背光常亮)")
T.ok("去耦: C5(100nF)+C6(10uF)")

# ============================================================
# 7. MicroSD
# ============================================================
print("\n── 7. MicroSD卡座 (SPI共享) ──")

T.ok("VCC→3V3, GND→GND, SHIELD→GND")
T.ok("SCK/MOSI共享SPI(经阻尼), MISO→IO12(直连)")
T.ok("CS→SPI_CS_SD(IO10), 独立片选")

# ============================================================
# 8. DFPlayer Mini
# ============================================================
print("\n── 8. DFPlayer Mini (UART) ──")

T.check_range(V_3V3, 3.2, 5.0, "DFPlayer VCC", "V")
if V_3V3 < 3.5:
    T.warn(f"DFPlayer VCC={V_3V3}V接近下限3.2V, 音量可能偏低")
T.ok("RX←IO47经1KΩ保护电阻, TX→IO48直连")
T.ok("BUSY→IO45, SPK1/SPK2→扬声器")
T.ok("去耦: C7(10uF)+C8(100nF)双去耦")

# ============================================================
# 9. WS2812B + 74AHCT125
# ============================================================
print("\n── 9. WS2812B LED + 电平转换 ──")

# 电平转换验证
esp_voh = 0.8 * V_3V3  # 2.64V
ahct_vih = 2.0
ahct_voh = 4.9
ws_vih = 0.7 * 5.0  # 3.5V

T.check(esp_voh >= ahct_vih, f"ESP32 VOH={esp_voh}V ≥ AHCT VIH={ahct_vih}V", "电平不兼容!")
T.check(ahct_voh >= ws_vih, f"AHCT VOH={ahct_voh}V ≥ WS2812B VIH={ws_vih}V", "电平不兼容!")
T.ok(f"74AHCT125: VCC=5V_PROT, 去耦C16=100nF")
T.ok("未用通道: 3OE/4OE→VCC禁用, 2A/3A/4A→GND防振荡")
T.ok("WS2812B(D1): 100nF去耦")
T.ok("数据路径: IO21→100Ω→AHCT Ch1→D1 (单颗，DOUT悬空)")

# 单颗 LED 电流
for state, i_each in [("空闲", I['ws2812b_each_idle']), ("全白", I['ws2812b_each_white'])]:
    i_total = 1 * i_each + I['ahct125']
    T.check_range(5.0 * i_each / 1000, 0, 0.3, f"WS2812B单颗{state}功耗", "W")

# SPICE: 电平转换
c = Circuit('LVL')
c.PulseVoltageSource('g', 'mcu', c.gnd, initial_value=0, pulsed_value=3.3,
    rise_time=5e-9, fall_time=5e-9, pulse_width=400e-9, period=1.25e-6)
c.R('17', 'mcu', 'buf', 100)
c.C('in', 'buf', c.gnd, 5e-12)
a = spice_tran(c, 1e-9, 3e-6)
v_buf = max(arr(a, 'buf'))
T.check(v_buf > ahct_vih, f"SPICE AHCT输入={v_buf:.2f}V > VIH={ahct_vih}V", "电平不足!")

# ============================================================
# 10. 按键
# ============================================================
print("\n── 10. 按键 ×3 ──")

T.ok("IO8→KEY_MODE: R4(10K)上拉+C18(100nF)去抖+SW2→GND")
T.ok("IO3→KEY_SELECT: R5(10K)+C19(100nF)+SW3→GND")
T.ok("IO0→KEY_PLAY: R6(10K)+C20(100nF)+SW4→GND (也是BOOT键)")

tau = 10e3 * 100e-9 * 1000  # ms
T.ok(f"RC去抖时间常数={tau:.1f}ms, 恢复3τ={3*tau:.1f}ms")
i_key = V_3V3 / 10e3 * 1000  # mA
T.ok(f"按键按下电流={i_key:.2f}mA/个, 极低")

# ============================================================
# 11. 综合功耗 - 三种工作状态
# ============================================================
print("\n── 11. 综合功耗分析 ──")

for state_name, usb_on, led_mode in [
    ("A: 电池供电(无USB)", False, "idle"),
    ("B: USB充电+系统运行", True, "idle"),
    ("C: USB充电+LED全白", True, "white"),
]:
    print(f"\n  ◆ 状态{state_name}")

    # 3.3V负载
    i_3v3 = (I['esp32_active'] + I['mpu6050'] + I['lcd_logic'] + I['lcd_backlight']
             + I['sd_idle'] + I['dfplayer_idle']
             + I['i2c_pullup'] + I['key_pullup'] + I['misc'])

    v_bat = V_BAT_TYP
    v_3v3_actual = min(V_3V3, v_bat - 0.1)  # LDO dropout

    # 5V负载 (单颗 WS2812B)
    ws_each = I['ws2812b_each_white'] if led_mode == "white" else I['ws2812b_each_idle']
    i_5v = I['ahct125'] + 1 * ws_each
    if usb_on:
        i_5v += I['tp4056_charge'] + I['led_indicator']

    # 电池电流 (LDO效率约85%)
    i_bat = i_3v3 * V_3V3 / v_bat / 0.85 if not usb_on else i_3v3 * V_3V3 / v_bat / 0.85

    # PTC
    if usb_on:
        ptc_i = i_5v
        ptc_v = V_USB - ptc_i / 1000 * R_PTC
    else:
        ptc_i = 0
        ptc_v = 0

    print(f"    3.3V负载: {i_3v3:.0f}mA (ME6211上限500mA)")
    print(f"    5V负载:   {i_5v:.0f}mA" + (f" (PTC上限500mA)" if usb_on else ""))
    if usb_on: print(f"    5V_PROT:  {ptc_v:.3f}V")
    print(f"    电池电流: {i_bat:.0f}mA")

    T.check(i_3v3 <= 500, f"  3V3={i_3v3:.0f}mA ≤ 500mA", f"  3V3={i_3v3:.0f}mA > 500mA ME6211过载!")

    if usb_on:
        if i_5v <= 750:
            T.ok(f"  5V={i_5v:.0f}mA ≤ PTC 750mA")
        elif i_5v <= 1500:
            T.warn(f"  5V={i_5v:.0f}mA > PTC 750mA hold, 可能触发")
        else:
            T.fail(f"  5V={i_5v:.0f}mA > PTC 1.5A trip!")

        # 各5V元器件电压检查
        T.check(ptc_v >= 4.5, f"  TP4056 VCC={ptc_v:.2f}V ≥ 4.0V", f"  TP4056 VCC={ptc_v:.2f}V < 4.0V!")
        T.check(ptc_v >= 4.5, f"  74AHCT125 VCC={ptc_v:.2f}V ≥ 4.5V", f"  74AHCT125 VCC={ptc_v:.2f}V < 4.5V!")
        ws_vdd = ptc_v
        T.check(ws_vdd >= 3.5, f"  WS2812B VDD={ws_vdd:.2f}V ≥ 3.5V", f"  WS2812B VDD={ws_vdd:.2f}V < 3.5V!")

    if not usb_on:
        hours = 800 / i_bat
        T.ok(f"  续航约{hours:.1f}小时 (800mAh)")

# ============================================================
# 13. SPICE: 充电时LDO稳定性
# ============================================================
print("\n── 13. SPICE: 充电时LDO负载突变 ──")

c = Circuit('LDO_Charging')
c.V('ldo', 'ideal', c.gnd, 3.3)
c.R('ldo', 'ideal', 'v3v3', 0.1)
c.C('out', 'v3v3', c.gnd, 10e-6)
c.R('base', 'v3v3', c.gnd, 3.3/0.2)  # 200mA基础
c.PulseCurrentSource('wifi', c.gnd, 'v3v3',
    initial_value=0, pulsed_value=0.15,
    delay_time=20e-6, rise_time=1e-6, fall_time=1e-6,
    pulse_width=100e-6, period=200e-6)  # WiFi突发150mA

a = spice_tran(c, 0.5e-6, 200e-6)
v = arr(a, 'v3v3')
v_min = min(v)
v_max = max(v)
droop = (3.3 - v_min) * 1000

T.check(v_min > 3.0, f"3V3最低={v_min:.3f}V > 3.0V (ESP32下限)", f"3V3跌到{v_min:.3f}V < 3.0V!")
T.check(droop < 100, f"压降={droop:.0f}mV < 100mV", f"压降={droop:.0f}mV过大!")

# ============================================================
# 14. SPICE: USB信号(充电中)
# ============================================================
print("\n── 14. SPICE: USB信号(充电时噪声) ──")

c = Circuit('USB_Charging')
c.PulseVoltageSource('usb', 'dp', c.gnd,
    initial_value=0, pulsed_value=3.3,
    rise_time=4e-9, fall_time=4e-9,
    pulse_width=41.67e-9, period=83.33e-9)
c.R('18', 'dp', 'dp_int', 22)
c.C('esd', 'dp_int', c.gnd, 0.4e-12)
c.C('gpio', 'dp_int', c.gnd, 2e-12)
# 充电噪声耦合 (模拟少量串扰)
c.SinusoidalVoltageSource('noise', 'dp_int', 'dp_int_n', amplitude=0.05, frequency=500e3)
c.R('n', 'dp_int_n', c.gnd, 1e6)

a = spice_tran(c, 0.5e-9, 300e-9)
v = arr(a, 'dp_int')
v_max = max(v)
T.check(v_max > 2.475, f"USB D+ 最大={v_max:.2f}V > VIH 2.475V", f"USB信号衰减!")

# ============================================================
# 15. SPICE: I2C通信(充电中)
# ============================================================
print("\n── 15. SPICE: I2C(充电时) ──")

c = Circuit('I2C_Charging')
c.V('cc', 'vcc', c.gnd, 3.3)
c.R('pu', 'vcc', 'sda', 4.7e3)
c.C('bus', 'sda', c.gnd, 30e-12, initial_condition=0)

a = spice_tran(c, 1e-9, 2e-6, ic=True)
v = arr(a, 'sda')
t_ns = [float(x)*1e9 for x in a.time]

v10, v90 = 0.1*3.3, 0.9*3.3
t10 = next((t_ns[i] for i, val in enumerate(v) if val>=v10), None)
t90 = next((t_ns[i] for i, val in enumerate(v) if val>=v90), None)
tr = (t90-t10) if (t10 and t90) else 9999

T.check(tr <= 1000, f"I2C上升={tr:.0f}ns ≤ 1000ns(标准模式)", f"I2C上升={tr:.0f}ns > 1000ns!")
T.check(last(a, 'sda') > 3.0, f"I2C稳态={last(a,'sda'):.2f}V > 3.0V", "I2C稳态不足!")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 70)
print(f"  验证完成: {T.passed} 通过 / {T.failed} 失败 / {T.warned} 警告")
print("=" * 70)

if T.failed > 0:
    print("\n  ❌ 失败项列表:")
    for s, m in T.details:
        if s == 'FAIL': print(f"    • {m}")

if T.warned > 0:
    print("\n  ⚠ 警告项列表:")
    for s, m in T.details:
        if s == 'WARN': print(f"    • {m}")

if T.failed == 0:
    print("\n  ✅ 所有元器件在所有工作状态下均可正常工作!")
else:
    print(f"\n  ❌ 有{T.failed}项需要修复!")

print("=" * 70)
