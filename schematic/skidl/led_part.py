"""
标准 LED 发光二极管 SKiDL 描述
用途：指示灯（充电指示、状态指示等）
封装：0805 或 直插 3mm/5mm
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_led(color='', ref_prefix='D'):
    """创建 LED 发光二极管"""
    
    led = Part(
        name='LED',
        value=color,
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix=ref_prefix,
        footprint='LED_SMD:LED_0805_2012Metric',
        description=f'{color} LED'
    )
    
    # LED 引脚
    led += Pin(num='1', name='A', func=Pin.types.PASSIVE)  # 阳极
    led += Pin(num='2', name='K', func=Pin.types.PASSIVE)  # 阴极
    
    return led

# 导出不同颜色的 LED
LED_RED = create_led('Red')     # 红色 LED
LED_GREEN = create_led('Green') # 绿色 LED
LED_BLUE = create_led('Blue')   # 蓝色 LED
LED_YELLOW = create_led('Yellow') # 黄色 LED
LED_WHITE = create_led('White') # 白色 LED
