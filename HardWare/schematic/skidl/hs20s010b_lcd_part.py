"""
HS20S010B LCD 显示屏模块 SKiDL 描述
型号：HS20S010B (2.0寸 TFT LCD)
驱动芯片：ST7789V2
字库芯片：GT30L32S4W
分辨率：240(H)RGB x 320(V)
接口：4线SPI + 字库引脚
制造商：深圳市汉昇实业有限公司

★ 引脚定义（根据实际封装图，20引脚，上下对称排列）
  上排引脚（Pin1-10，从左到右）：
    Pin1: GND, Pin2: VCC, Pin3: CLK, Pin4: SDA, Pin5: RES
    Pin6: DC, Pin7: CS1, Pin8: BLK, Pin9: FS0, Pin10: FCS
  
  下排引脚（Pin11-20，从右到左）：
    Pin11: VCC, Pin12: GND, Pin13: BLA, Pin14: FCS, Pin15: FS0
    Pin16: CLK, Pin17: SDA, Pin18: DC, Pin19: RES, Pin20: CS1
  
  注意：上下排有重复的引脚名称，实际使用时只需连接上排或下排即可
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_hs20s010b_lcd():
    """创建 HS20S010B LCD 显示屏模块（20引脚）"""
    
    lcd = Part(
        name='HS20S010B_LCD',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='LCD',
        footprint='Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical',
        description='HS20S010B 2.0 inch TFT LCD, 240x320, ST7789V2 driver, GT30L32S4W font IC, 20-pin'
    )
    
    # ★ 上排引脚（Pin1-10，从左到右）
    lcd += Pin(num='1', name='GND', func=Pin.types.PWRIN)      # Pin1: GND
    lcd += Pin(num='2', name='VCC', func=Pin.types.PWRIN)      # Pin2: VCC
    lcd += Pin(num='3', name='CLK', func=Pin.types.INPUT)      # Pin3: CLK (SPI时钟)
    lcd += Pin(num='4', name='SDA', func=Pin.types.BIDIR)      # Pin4: SDA (SPI数据)
    lcd += Pin(num='5', name='RES', func=Pin.types.INPUT)      # Pin5: RES (复位)
    lcd += Pin(num='6', name='DC', func=Pin.types.INPUT)       # Pin6: DC (数据/命令)
    lcd += Pin(num='7', name='CS1', func=Pin.types.INPUT)      # Pin7: CS1 (片选)
    lcd += Pin(num='8', name='BLK', func=Pin.types.INPUT)      # Pin8: BLK (背光控制)
    lcd += Pin(num='9', name='FS0', func=Pin.types.OUTPUT)      # Pin9: FS0 (字库相关)
    lcd += Pin(num='10', name='FCS', func=Pin.types.INPUT)     # Pin10: FCS (字库片选)
    
    # ★ 下排引脚（Pin11-20，从右到左）
    lcd += Pin(num='11', name='VCC_B', func=Pin.types.PWRIN)    # Pin11: VCC (下排)
    lcd += Pin(num='12', name='GND_B', func=Pin.types.PWRIN)    # Pin12: GND (下排)
    lcd += Pin(num='13', name='BLA', func=Pin.types.INPUT)     # Pin13: BLA (背光阳极)
    lcd += Pin(num='14', name='FCS_B', func=Pin.types.INPUT)    # Pin14: FCS (下排)
    lcd += Pin(num='15', name='FS0_B', func=Pin.types.OUTPUT)  # Pin15: FS0 (下排)
    lcd += Pin(num='16', name='CLK_B', func=Pin.types.INPUT)   # Pin16: CLK (下排)
    lcd += Pin(num='17', name='SDA_B', func=Pin.types.BIDIR)    # Pin17: SDA (下排)
    lcd += Pin(num='18', name='DC_B', func=Pin.types.INPUT)     # Pin18: DC (下排)
    lcd += Pin(num='19', name='RES_B', func=Pin.types.INPUT)    # Pin19: RES (下排)
    lcd += Pin(num='20', name='CS1_B', func=Pin.types.INPUT)    # Pin20: CS1 (下排)
    
    return lcd

# 导出模板
HS20S010B_LCD = create_hs20s010b_lcd()

# 为了向后兼容，也导出为ST7789_LCD别名
ST7789_LCD = HS20S010B_LCD
