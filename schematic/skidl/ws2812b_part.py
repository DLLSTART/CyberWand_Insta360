"""
WS2812B RGB LED SKiDL 描述
型号：WS2812B
制造商：WorldSemi
封装：5050 (5x5mm)
接口：单线数字控制
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_ws2812b():
    """创建 WS2812B LED"""
    
    led = Part(
        name='WS2812B',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='D',
        footprint='LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm',
        description='WS2812B RGB LED'
    )
    
    # 电源引脚
    led += Pin(num='1', name='VDD', func=Pin.types.PWRIN)
    led += Pin(num='3', name='GND', func=Pin.types.PWRIN)
    
    # 数据引脚
    led += Pin(num='4', name='DIN', func=Pin.types.INPUT)
    led += Pin(num='2', name='DOUT', func=Pin.types.OUTPUT)
    
    return led

# 导出模板
WS2812B = create_ws2812b()
