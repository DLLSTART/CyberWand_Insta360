"""
INMP441 MEMS 麦克风 SKiDL 描述
型号：INMP441
制造商：TDK/InvenSense
接口：I2S
ADC分辨率：24位
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_inmp441():
    """创建 INMP441 麦克风"""
    
    mic = Part(
        name='INMP441',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='MIC',
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
        description='INMP441 MEMS Microphone Module'
    )
    
    # 电源引脚
    mic += Pin(num='1', name='VDD', func=Pin.types.PWRIN)
    mic += Pin(num='2', name='GND', func=Pin.types.PWRIN)
    
    # I2S 接口
    mic += Pin(num='3', name='SCK', func=Pin.types.INPUT)
    mic += Pin(num='4', name='SD', func=Pin.types.OUTPUT)
    mic += Pin(num='5', name='WS', func=Pin.types.INPUT)
    
    # 声道选择
    mic += Pin(num='6', name='L_R', func=Pin.types.INPUT)
    
    return mic

# 导出模板
INMP441 = create_inmp441()
