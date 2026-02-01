"""
ST7789 LCD 显示屏模块 SKiDL 描述
型号：HS20HS072RX (1.8寸 TFT LCD)
驱动芯片：ST7789
分辨率：128x160
接口：SPI
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_st7789_lcd():
    """创建 ST7789 LCD 显示屏"""
    
    lcd = Part(
        name='ST7789_LCD',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='LCD',
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',
        description='ST7789 1.8 inch TFT LCD'
    )
    
    # 电源引脚
    lcd += Pin(num='1', name='VCC', func=Pin.types.PWRIN)
    lcd += Pin(num='2', name='GND', func=Pin.types.PWRIN)
    
    # SPI 接口
    lcd += Pin(num='3', name='CS', func=Pin.types.INPUT)
    lcd += Pin(num='4', name='SCK', func=Pin.types.INPUT)
    lcd += Pin(num='5', name='MOSI', func=Pin.types.INPUT)
    
    # 控制引脚
    lcd += Pin(num='6', name='DC', func=Pin.types.INPUT)
    lcd += Pin(num='7', name='RST', func=Pin.types.INPUT)
    lcd += Pin(num='8', name='BL', func=Pin.types.INPUT)  # 背光控制
    
    return lcd

# 导出模板
ST7789_LCD = create_st7789_lcd()
