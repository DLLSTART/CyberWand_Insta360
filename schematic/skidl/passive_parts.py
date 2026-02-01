"""
被动元器件 SKiDL 描述
包括：电阻、电容、按键等
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_resistor(value, ref_prefix='R'):
    """创建电阻"""
    r = Part(
        name='R',
        value=value,
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='Resistor_SMD:R_0603_1608Metric'
    )
    r += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    r += Pin(num='2', name='2', func=Pin.types.PASSIVE)
    return r

def create_capacitor(value, ref_prefix='C'):
    """创建电容"""
    c = Part(
        name='C',
        value=value,
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='Capacitor_SMD:C_0603_1608Metric'
    )
    c += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    c += Pin(num='2', name='2', func=Pin.types.PASSIVE)
    return c

def create_switch(ref_prefix='SW'):
    """创建轻触按键"""
    sw = Part(
        name='SW_Push',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='Button_Switch_SMD:SW_SPST_TL3342'
    )
    sw += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    sw += Pin(num='2', name='2', func=Pin.types.PASSIVE)
    return sw

def create_speaker(ref_prefix='LS'):
    """创建扬声器"""
    spk = Part(
        name='Speaker',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal'
    )
    spk += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    spk += Pin(num='2', name='2', func=Pin.types.PASSIVE)
    return spk

# 导出常用值
R_10K = create_resistor('10k')
R_4K7 = create_resistor('4.7k')
R_2K = create_resistor('2k')
R_5K1 = create_resistor('5.1k')
R_1K = create_resistor('1k')   # LED 限流电阻
C_100N = create_capacitor('100nF')
C_10U = create_capacitor('10uF')
SWITCH = create_switch()
SPEAKER = create_speaker()
