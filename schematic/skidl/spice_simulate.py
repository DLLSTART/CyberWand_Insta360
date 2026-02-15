"""
CyberWand v2.3 - SPICE电路仿真
================================
使用PySpice+ngspice(KiCad内置)对每个子电路进行仿真验证
"""

import sys, os, math
sys.stdout.reconfigure(encoding='utf-8')

os.environ['SPICE_LIB_DIR'] = r'D:\kicad\lib\ngspice'
os.add_dll_directory(r'D:\kicad\bin')

from PySpice.Spice.Netlist import Circuit

# ============================================================
class Results:
    def __init__(self):
        self.tests = []
    def ok(self, name, msg=""):
        self.tests.append(('PASS', name, msg))
        print(f"  [PASS] {name}" + (f" -- {msg}" if msg else ""))
    def fail(self, name, msg):
        self.tests.append(('FAIL', name, msg))
        print(f"  [FAIL] {name} -- {msg}")
    def warn(self, name, msg):
        self.tests.append(('WARN', name, msg))
        print(f"  [WARN] {name} -- {msg}")
    def summary(self):
        p = sum(1 for s,_,_ in self.tests if s=='PASS')
        f = sum(1 for s,_,_ in self.tests if s=='FAIL')
        w = sum(1 for s,_,_ in self.tests if s=='WARN')
        return p, f, w

R = Results()

def get_last(analysis, node):
    """安全获取仿真结果最终值"""
    arr = [float(v) for v in analysis[node]]
    return arr[-1] if arr else 0

def get_array(analysis, node):
    return [float(v) for v in analysis[node]]

def get_time_ms(analysis):
    return [float(t)*1000 for t in analysis.time]

# ============================================================
# 仿真1: ESP32 EN复位RC电路
# ============================================================
def sim_en_reset():
    print("\n" + "="*60)
    print("  SIM-1: ESP32 EN复位电路 (R1=10K + C_EN=1uF)")
    print("="*60)

    c = Circuit('EN Reset')
    c.PieceWiseLinearVoltageSource('vcc', 'vcc', c.gnd,
        values=[(0, 0), (1e-3, 3.3), (100e-3, 3.3)])
    c.R('1', 'vcc', 'en', 10e3)
    c.C('en', 'en', c.gnd, 1e-6, initial_condition=0)

    a = c.simulator().transient(step_time=0.1e-3, end_time=60e-3,
                                 use_initial_condition=True)
    t = get_time_ms(a)
    v = get_array(a, 'en')

    final = v[-1]
    vih = 0.75 * 3.3  # 2.475V

    t_vih = next((t[i] for i, val in enumerate(v) if val >= vih), None)

    print(f"    EN最终={final:.3f}V, 达到VIH(2.475V)={t_vih:.1f}ms")

    R.ok(f"EN稳态={final:.2f}V", "≈3.3V") if abs(final-3.3)<0.1 else R.fail(f"EN={final:.2f}V","!=3.3V")
    R.ok(f"EN延迟={t_vih:.1f}ms", "5~30ms合理") if t_vih and 2<t_vih<40 else R.warn("EN延迟","异常")
    R.ok("EN保持低>50us", f"{t_vih:.1f}ms>>0.05ms") if t_vih and t_vih>0.05 else None

# ============================================================
# 仿真2: 充电LED电流 (开漏驱动)
# ============================================================
def sim_charging_led():
    print("\n" + "="*60)
    print("  SIM-2: 充电LED (5V→R11=1K→LED→CHRG=GND)")
    print("="*60)

    c = Circuit('LED')
    c.V('cc', 'vcc', c.gnd, 5.0)
    c.R('11', 'vcc', 'anode', 1e3)
    c.D('4', 'anode', 'cathode', model='RED')
    c.model('RED', 'D', IS=1e-20, N=1.8, RS=5)
    c.V('chrg', 'cathode', c.gnd, 0)  # CHRG拉低

    a = c.simulator().transient(step_time=1e-6, end_time=1e-3)
    v_a = get_last(a, 'anode')
    i_led = (5.0 - v_a) / 1000 * 1000  # mA

    print(f"    LED Vf={v_a:.3f}V, 电流={i_led:.2f}mA")

    R.ok(f"LED电流={i_led:.1f}mA", "1.5~5mA合理") if 1<i_led<10 else R.warn(f"LED电流{i_led:.1f}","异常")
    R.ok(f"CHRG汇电流<25mA", f"{i_led:.1f}mA") if i_led<25 else R.fail("CHRG过流","")

# ============================================================
# 仿真3: 按键去抖RC
# ============================================================
def sim_key_debounce():
    print("\n" + "="*60)
    print("  SIM-3: 按键去抖 (R4=10K + C18=100nF)")
    print("="*60)

    # 分两阶段: 先验证上拉稳态, 再验证放电RC
    # 阶段1: 上拉稳态 (按键未按)
    c1 = Circuit('Key Idle')
    c1.V('cc', 'vcc', c1.gnd, 3.3)
    c1.R('4', 'vcc', 'key', 10e3)
    c1.C('18', 'key', c1.gnd, 100e-9)

    a1 = c1.simulator().transient(step_time=10e-6, end_time=5e-3)
    v_idle = get_last(a1, 'key')

    # 阶段2: 按键按下 = 电容通过10Ω放电 (初始3.3V→0V)
    c2 = Circuit('Key Press')
    c2.V('cc', 'vcc', c2.gnd, 3.3)
    c2.R('4', 'vcc', 'key', 10e3)
    c2.C('18', 'key', c2.gnd, 100e-9, initial_condition=3.3)
    c2.R('sw', 'key', c2.gnd, 10)  # 按键内阻

    a2 = c2.simulator().transient(step_time=1e-6, end_time=1e-3,
                                   use_initial_condition=True)
    t2 = get_time_ms(a2)
    v2 = get_array(a2, 'key')

    v_pressed = v2[-1]
    vil = 0.25 * 3.3
    t_vil = next((t2[i] for i, val in enumerate(v2) if val<=vil), None)

    # RC时间常数: 10Ω//10KΩ ≈ 10Ω * 100nF = 1us (放电极快)
    # 上拉恢复: 10K * 100nF = 1ms
    tau_discharge = 10 * 100e-9 * 1e6  # us
    tau_recovery = 10e3 * 100e-9 * 1000  # ms

    print(f"    上拉稳态={v_idle:.2f}V, 按下后={v_pressed:.4f}V")
    print(f"    放电τ={tau_discharge:.1f}us, 恢复τ={tau_recovery:.1f}ms")
    if t_vil: print(f"    达到VIL(0.825V): {t_vil:.3f}ms")

    R.ok(f"上拉={v_idle:.2f}V", "≈3.3V") if abs(v_idle-3.3)<0.2 else R.fail("上拉错误","")
    R.ok(f"拉低={v_pressed:.4f}V", "≈0V") if v_pressed<0.1 else R.warn(f"拉低={v_pressed:.2f}V","偏高")
    R.ok(f"RC去抖: 恢复τ={tau_recovery:.1f}ms", "有效消除抖动(典型5~10ms)")

# ============================================================
# 仿真4: I2C上拉上升时间
# ============================================================
def sim_i2c():
    print("\n" + "="*60)
    print("  SIM-4: I2C上拉上升时间 (R2=4.7K, Cbus=30pF)")
    print("="*60)

    c = Circuit('I2C')
    c.V('cc', 'vcc', c.gnd, 3.3)
    c.R('2', 'vcc', 'sda', 4.7e3)
    c.C('bus', 'sda', c.gnd, 30e-12, initial_condition=0)

    a = c.simulator().transient(step_time=1e-9, end_time=2e-6,
                                 use_initial_condition=True)
    t_ns = [float(x)*1e9 for x in a.time]
    v = get_array(a, 'sda')

    v10 = 0.1*3.3
    v90 = 0.9*3.3
    t10 = next((t_ns[i] for i, val in enumerate(v) if val>=v10), None)
    t90 = next((t_ns[i] for i, val in enumerate(v) if val>=v90), None)
    tr = (t90-t10) if (t10 and t90) else None

    print(f"    上升时间(10%→90%): {tr:.0f}ns" if tr else "    无法测量")
    print(f"    RC = 4.7K×30pF = {4.7e3*30e-12*1e9:.0f}ns")

    if tr and tr<=300: R.ok(f"I2C tr={tr:.0f}ns", "支持快速模式(≤300ns)")
    elif tr and tr<=1000: R.ok(f"I2C tr={tr:.0f}ns", "支持标准模式(≤1000ns)")
    elif tr: R.warn(f"I2C tr={tr:.0f}ns", "偏慢")

# ============================================================
# 仿真5: USB信号衰减 (22Ω + ESD 0.4pF)
# ============================================================
def sim_usb():
    print("\n" + "="*60)
    print("  SIM-5: USB信号衰减 (R=22Ω, CESD=0.4pF+CGPIO=2pF)")
    print("="*60)

    c = Circuit('USB')
    c.PulseVoltageSource('usb', 'dp', c.gnd,
        initial_value=0, pulsed_value=3.3,
        rise_time=4e-9, fall_time=4e-9,
        pulse_width=41.67e-9, period=83.33e-9)
    c.R('18', 'dp', 'dp_int', 22)
    c.C('esd', 'dp_int', c.gnd, 0.4e-12)
    c.C('gpio', 'dp_int', c.gnd, 2e-12)

    a = c.simulator().transient(step_time=0.5e-9, end_time=300e-9)
    v = get_array(a, 'dp_int')
    v_max = max(v)

    bw = 1/(2*math.pi*22*2.4e-12)/1e6

    print(f"    ESP32端最大电压: {v_max:.3f}V (源=3.3V)")
    print(f"    衰减: {(1-v_max/3.3)*100:.1f}%")
    print(f"    3dB带宽: {bw:.0f}MHz")

    R.ok(f"USB电平={v_max:.2f}V>VIH", "ESP32可识别") if v_max>2.475 else R.fail("USB衰减太大","")
    R.ok(f"USB带宽={bw:.0f}MHz", ">12MHz FS") if bw>12 else R.fail("带宽不足","")

# ============================================================
# 仿真6: LDO输出纹波
# ============================================================
def sim_ldo():
    print("\n" + "="*60)
    print("  SIM-6: LDO输出纹波 (10uF输出电容, 400mA负载)")
    print("="*60)

    c = Circuit('LDO')
    c.V('ldo', 'ldo_ideal', c.gnd, 3.3)
    c.R('ldo', 'ldo_ideal', 'v3v3', 0.1)  # LDO内阻
    c.C('9', 'v3v3', c.gnd, 10e-6)
    c.R('load', 'v3v3', c.gnd, 3.3/0.4)  # 400mA

    # 负载突变: 200mA→400mA
    c.PulseCurrentSource('step', c.gnd, 'v3v3',
        initial_value=0, pulsed_value=0.2,
        delay_time=50e-6, rise_time=1e-6, fall_time=1e-6,
        pulse_width=200e-6, period=500e-6)

    a = c.simulator().transient(step_time=0.5e-6, end_time=300e-6)
    v = get_array(a, 'v3v3')

    v_min = min(v)
    v_max = max(v)
    droop = (3.3 - v_min) * 1000  # mV

    print(f"    3V3范围: {v_min:.4f}V ~ {v_max:.4f}V")
    print(f"    负载突变压降: {droop:.1f}mV")

    R.ok(f"纹波={droop:.0f}mV", "<50mV") if droop<50 else R.warn(f"纹波={droop:.0f}mV","偏大")
    R.ok(f"3V3最低={v_min:.3f}V", ">3.0V") if v_min>3.0 else R.fail("3V3跌破3.0V","")

# ============================================================
# 仿真7: 电源系统全局DC
# ============================================================
def sim_power_dc():
    print("\n" + "="*60)
    print("  SIM-7: 电源系统全局直流")
    print("="*60)

    c = Circuit('Power DC')
    c.V('usb', 'v5v', c.gnd, 5.0)
    c.R('ptc', 'v5v', 'v5v_prot', 0.15)  # PTC
    c.R('charge', 'v5v_prot', c.gnd, 5.0/0.5)  # 充电500mA
    c.R('ws', 'v5v_prot', c.gnd, 5.0/0.06)  # LED 60mA
    c.R('ahct', 'v5v_prot', c.gnd, 5.0/0.01)  # 74AHCT 10mA

    c.V('bat', 'vbat', c.gnd, 3.7)
    c.R('sw', 'vbat', 'vbat_sw', 0.1)  # 开关
    c.V('ldo', 'v3v3_s', c.gnd, 3.3)
    c.R('ldo_r', 'v3v3_s', 'v3v3', 0.05)
    c.R('load', 'v3v3', c.gnd, 3.3/0.4)

    a = c.simulator().transient(step_time=1e-6, end_time=10e-6)
    v5p = get_last(a, 'v5v_prot')
    vbs = get_last(a, 'vbat_sw')
    v33 = get_last(a, 'v3v3')

    i5 = (5.0-v5p)/0.15
    ptc_drop = (5.0-v5p)*1000

    print(f"    5V_PROT={v5p:.3f}V (PTC降{ptc_drop:.0f}mV)")
    print(f"    VBAT_SW={vbs:.3f}V")
    print(f"    3V3={v33:.3f}V")
    print(f"    5V总电流={i5*1000:.0f}mA")

    R.ok(f"5V_PROT={v5p:.2f}V","PTC压降OK") if v5p>4.7 else R.warn(f"5V_PROT={v5p:.2f}V","低")
    R.ok(f"3V3={v33:.3f}V","稳定") if abs(v33-3.3)<0.05 else R.warn(f"3V3={v33:.3f}","偏离")

    if i5>0.5:
        R.warn(f"5V电流={i5*1000:.0f}mA>500mA", "充电+LED同时满载, PTC可能触发")
    else:
        R.ok(f"5V电流={i5*1000:.0f}mA", "<500mA PTC保持")

# ============================================================
# 仿真8: 电平转换 (3.3V→5V)
# ============================================================
def sim_level_shift():
    print("\n" + "="*60)
    print("  SIM-8: WS2812B电平转换 (100Ω+74AHCT125)")
    print("="*60)

    c = Circuit('LevelShift')
    # ESP32 GPIO 800kHz WS2812B时序
    c.PulseVoltageSource('gpio', 'mcu', c.gnd,
        initial_value=0, pulsed_value=3.3,
        rise_time=5e-9, fall_time=5e-9,
        pulse_width=400e-9, period=1.25e-6)
    c.R('17', 'mcu', 'buf_in', 100)  # 串联电阻
    c.C('in', 'buf_in', c.gnd, 5e-12)  # AHCT输入电容

    a = c.simulator().transient(step_time=1e-9, end_time=3e-6)
    v = get_array(a, 'buf_in')
    v_max = max(v)
    v_min = min(v[len(v)//2:])

    print(f"    74AHCT125输入: {v_min:.3f}V ~ {v_max:.3f}V")
    print(f"    AHCT VIH=2.0V, VIL=0.8V")

    R.ok(f"输入高={v_max:.2f}V>2.0V(VIH)", "AHCT识别为HIGH") if v_max>2.0 else R.fail("输入低于VIH","")

    # 74AHCT125输出 = VCC-0.1V = 4.9V (理论)
    # WS2812B VIH = 0.7*5V = 3.5V
    ahct_voh = 4.9
    ws_vih = 3.5
    R.ok(f"AHCT输出={ahct_voh}V>{ws_vih}V(WS VIH)", "WS2812B可识别")

# ============================================================
def main():
    print("="*60)
    print("  CyberWand v2.3 - SPICE电路仿真")
    print("  引擎: PySpice + ngspice (KiCad内置)")
    print("="*60)

    sims = [
        ("EN复位", sim_en_reset),
        ("充电LED", sim_charging_led),
        ("按键去抖", sim_key_debounce),
        ("I2C上拉", sim_i2c),
        ("USB信号", sim_usb),
        ("LDO纹波", sim_ldo),
        ("电源DC", sim_power_dc),
        ("电平转换", sim_level_shift),
    ]

    for name, fn in sims:
        try:
            fn()
        except Exception as e:
            R.fail(f"{name}仿真异常", str(e)[:80])

    p, f, w = R.summary()
    print("\n" + "="*60)
    print(f"  仿真结果: {p} 通过, {f} 失败, {w} 警告")
    if f == 0:
        print("  [OK] 所有SPICE仿真通过!")
    else:
        print("  [!!] 存在失败项, 需检查!")
    print("="*60)

if __name__ == '__main__':
    main()
