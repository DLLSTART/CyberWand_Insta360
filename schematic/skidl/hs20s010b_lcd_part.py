"""
HS20S010B LCD 显示屏模块 SKiDL 描述
型号：HS20S010B (2.0寸 TFT LCD)
驱动芯片：ST7789V2
字库芯片：GT30L32S4W
分辨率：240(H)RGB x 320(V)
接口：4线SPI + 字库引脚
制造商：深圳市汉昇实业有限公司
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_hs20s010b_lcd():
    """创建 HS20S010B LCD 显示屏模块"""
    
    lcd = Part(
        name='HS20S010B_LCD',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='LCD',
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical',
        description='HS20S010B 2.0 inch TFT LCD, 240x320, ST7789V2 driver, GT30L32S4W font IC'
    )
    
    # 引脚1: GND - 地
    lcd += Pin(num='1', name='GND', func=Pin.types.PWRIN)
    
    # 引脚2: VCC - 电源（3.3V）
    lcd += Pin(num='2', name='VCC', func=Pin.types.PWRIN)
    
    # 引脚3: SCL - SPI时钟
    lcd += Pin(num='3', name='SCL', func=Pin.types.INPUT)
    
    # 引脚4: SDA - SPI数据
    lcd += Pin(num='4', name='SDA', func=Pin.types.BIDIR)
    
    # 引脚5: RES - 复位（低电平有效）
    lcd += Pin(num='5', name='RES', func=Pin.types.INPUT)
    
    # 引脚6: DC - 数据/命令选择
    lcd += Pin(num='6', name='DC', func=Pin.types.INPUT)
    
    # 引脚7: CS - LCD芯片选择（低电平使能）
    lcd += Pin(num='7', name='CS', func=Pin.types.INPUT)
    
    # 引脚8: BLK - 背光控制（默认开启，低电平关闭）
    lcd += Pin(num='8', name='BLK', func=Pin.types.INPUT)
    
    # 引脚9: FSO - 字库数据输出（可选，如不使用字库可悬空）
    lcd += Pin(num='9', name='FSO', func=Pin.types.OUTPUT)
    
    # 引脚10: FCS - 字库IC片选（低电平使能，可选）
    lcd += Pin(num='10', name='FCS', func=Pin.types.INPUT)
    
    return lcd

# 导出模板
HS20S010B_LCD = create_hs20s010b_lcd()

# 为了向后兼容，也导出为ST7789_LCD别名
ST7789_LCD = HS20S010B_LCD
