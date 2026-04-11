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
R_1K = create_resistor('1k')       # LED 限流电阻
R_33 = create_resistor('33')       # SPI 阻尼电阻 (信号完整性)
R_100 = create_resistor('100')     # WS2812B 数据线串联电阻
R_22 = create_resistor('22')       # USB 数据线串联电阻 (阻抗匹配)
C_2N2 = create_capacitor('2.2nF')   # MPU6050 CPOUT 电荷泵
C_100N = create_capacitor('100nF')
C_10U = create_capacitor('10uF')
C_1U = create_capacitor('1uF')     # ESP32 EN复位延迟 / 通用
C_22U = create_capacitor('22uF')   # 电源储能电容 (大容量)
SWITCH = create_switch()
SPEAKER = create_speaker()

def create_pin_header_1x03(ref_prefix='J'):
    """1x3 排针，用于调试串口等 (Pin1=TX, Pin2=RX, Pin3=GND)"""
    p = Part(
        name='Conn_01x03',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'
    )
    p += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    p += Pin(num='2', name='2', func=Pin.types.PASSIVE)
    p += Pin(num='3', name='3', func=Pin.types.PASSIVE)
    return p

PIN_HEADER_1X03 = create_pin_header_1x03()
