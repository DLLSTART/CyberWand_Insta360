"""
DFPlayer Mini 音频播放模块 SKiDL 描述
型号：DFPlayer Mini
接口：UART (串口)
支持格式：MP3, WAV
功放功率：3W
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_dfplayer_mini():
    """创建 DFPlayer Mini 模块"""
    
    dfplayer = Part(
        name='DFPlayer_Mini',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical',
        description='DFPlayer Mini MP3 Module'
    )
    
    # 电源引脚
    dfplayer += Pin(num='1', name='VCC', func=Pin.types.PWRIN)
    dfplayer += Pin(num='7', name='GND', func=Pin.types.PWRIN)
    
    # UART 接口
    dfplayer += Pin(num='2', name='RX', func=Pin.types.INPUT)
    dfplayer += Pin(num='3', name='TX', func=Pin.types.OUTPUT)
    
    # 状态引脚
    dfplayer += Pin(num='16', name='BUSY', func=Pin.types.OUTPUT)
    
    # 扬声器输出
    dfplayer += Pin(num='8', name='SPK1', func=Pin.types.OUTPUT)
    dfplayer += Pin(num='9', name='SPK2', func=Pin.types.OUTPUT)
    
    # 其他引脚（未使用）
    dfplayer += Pin(num='4', name='DAC_R', func=Pin.types.OUTPUT)
    dfplayer += Pin(num='5', name='DAC_L', func=Pin.types.OUTPUT)
    dfplayer += Pin(num='11', name='IO1', func=Pin.types.BIDIR)
    dfplayer += Pin(num='12', name='IO2', func=Pin.types.BIDIR)
    dfplayer += Pin(num='13', name='ADKEY1', func=Pin.types.INPUT)
    dfplayer += Pin(num='14', name='ADKEY2', func=Pin.types.INPUT)
    dfplayer += Pin(num='15', name='USB_P', func=Pin.types.BIDIR)
    
    return dfplayer

# 导出模板
DFPLAYER_MINI = create_dfplayer_mini()
