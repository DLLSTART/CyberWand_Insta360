"""
MicroSD 卡座 SKiDL 描述
接口：SPI
支持：MicroSD 卡（最大32GB）
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_microsd_socket():
    """创建 MicroSD 卡座"""
    
    sd = Part(
        name='MicroSD_Socket',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='J',
        footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',
        description='MicroSD Socket with SPI'
    )
    
    # 电源引脚
    sd += Pin(num='4', name='VCC', func=Pin.types.PWRIN)
    sd += Pin(num='3', name='GND', func=Pin.types.PWRIN)
    
    # SPI 接口
    sd += Pin(num='2', name='CS', func=Pin.types.INPUT)
    sd += Pin(num='5', name='SCK', func=Pin.types.INPUT)
    sd += Pin(num='7', name='MOSI', func=Pin.types.INPUT)
    sd += Pin(num='8', name='MISO', func=Pin.types.TRISTATE)  # 三态输出，支持SPI总线共享
    
    # 卡检测（可选）
    sd += Pin(num='9', name='CD', func=Pin.types.PASSIVE)
    
    # 屏蔽
    sd += Pin(num='1', name='SHIELD', func=Pin.types.PASSIVE)
    
    return sd

# 导出模板
MICROSD_SOCKET = create_microsd_socket()
