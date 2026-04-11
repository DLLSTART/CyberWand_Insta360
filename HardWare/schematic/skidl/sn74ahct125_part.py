"""
SN74AHCT125 四路电平转换缓冲器 SKiDL 描述
型号：SN74AHCT125D (SOIC-14)
制造商：Texas Instruments
封装：SOIC-14
描述：3.3V→5V 电平转换器，适合 WS2812B LED 数据驱动
    - 4路独立通道
    - VIL = 0.8V, VIH = 2.0V (AHCT阈值，完美支持3.3V输入)
    - VOH = VCC - 0.1V ≈ 4.9V (驱动5V逻辑)
    - 传播延迟: 7.5ns 典型
    - 电源电压: 4.5V ~ 5.5V
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_sn74ahct125():
    """创建 SN74AHCT125 电平转换缓冲器"""

    buf = Part(
        name='SN74AHCT125',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
        description='74AHCT125 Quad Level-Shifter 3.3V to 5V, SOIC-14'
    )

    # 电源引脚
    buf += Pin(num='14', name='VCC', func=Pin.types.PWRIN)    # 5V电源
    buf += Pin(num='7', name='GND', func=Pin.types.PWRIN)     # 地

    # 通道1: 1OE#(低有效), 1A(输入), 1Y(输出)
    buf += Pin(num='1', name='1OE', func=Pin.types.INPUT)     # 输出使能(低有效)
    buf += Pin(num='2', name='1A', func=Pin.types.INPUT)      # 数据输入
    buf += Pin(num='3', name='1Y', func=Pin.types.OUTPUT)     # 数据输出

    # 通道2
    buf += Pin(num='4', name='2OE', func=Pin.types.INPUT)
    buf += Pin(num='5', name='2A', func=Pin.types.INPUT)
    buf += Pin(num='6', name='2Y', func=Pin.types.OUTPUT)

    # 通道3
    buf += Pin(num='9', name='3OE', func=Pin.types.INPUT)
    buf += Pin(num='8', name='3A', func=Pin.types.INPUT)
    buf += Pin(num='10', name='3Y', func=Pin.types.OUTPUT)

    # 通道4
    buf += Pin(num='12', name='4OE', func=Pin.types.INPUT)
    buf += Pin(num='11', name='4A', func=Pin.types.INPUT)
    buf += Pin(num='13', name='4Y', func=Pin.types.OUTPUT)

    return buf

# 导出模板
SN74AHCT125 = create_sn74ahct125()
