"""
ESP32-S3-WROOM-1N16R8 模块 SKiDL 描述
型号：ESP32-S3-WROOM-1N16R8
制造商：Espressif (乐鑫)
封装：SMD, 18.0x25.5mm
描述：双核Xtensa LX7处理器，240MHz，16MB Flash + 8MB PSRAM
注意：
1. 这是一个完整的模块，包含ESP32-S3芯片、Flash、PSRAM和天线
2. IO35(28), IO36(29), IO37(30) 已被内部PSRAM占用，不可外部使用
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

# 创建 ESP32-S3-WROOM-1N16R8 模块模板
def create_esp32_s3_wroom():
    """创建 ESP32-S3-WROOM-1N16R8 模块"""
    
    # 使用 Part 创建元器件实例（不依赖外部库）
    esp32 = Part(
        name='ESP32-S3-WROOM-1',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='RF_Module:ESP32-S3-WROOM-1',
        description='ESP32-S3 Module with 16MB Flash + 8MB PSRAM'
    )
    
    # 电源和地引脚
    esp32 += Pin(num='1', name='GND1', func=Pin.types.PWRIN)
    esp32 += Pin(num='2', name='3V3', func=Pin.types.PWRIN)
    esp32 += Pin(num='3', name='EN', func=Pin.types.INPUT)
    esp32 += Pin(num='40', name='GND2', func=Pin.types.PWRIN)
    esp32 += Pin(num='41', name='EPAD', func=Pin.types.PWRIN)
    
    # GPIO 引脚 (左侧 4-20)
    esp32 += Pin(num='4', name='IO4', func=Pin.types.BIDIR)    # ADC1_CH3, TOUCH4
    esp32 += Pin(num='5', name='IO5', func=Pin.types.BIDIR)    # ADC1_CH4, TOUCH5
    esp32 += Pin(num='6', name='IO6', func=Pin.types.BIDIR)    # ADC1_CH5, TOUCH6
    esp32 += Pin(num='7', name='IO7', func=Pin.types.BIDIR)    # ADC1_CH6, TOUCH7
    esp32 += Pin(num='8', name='IO15', func=Pin.types.BIDIR)   # ADC2_CH4, U0RTS
    esp32 += Pin(num='9', name='IO16', func=Pin.types.BIDIR)   # ADC2_CH5, U0CTS
    esp32 += Pin(num='10', name='IO17', func=Pin.types.BIDIR)  # ADC2_CH6, U1TXD
    esp32 += Pin(num='11', name='IO18', func=Pin.types.BIDIR)  # ADC2_CH7, U1RXD, USB_D-
    esp32 += Pin(num='12', name='IO8', func=Pin.types.BIDIR)   # ADC1_CH7, TOUCH8
    esp32 += Pin(num='13', name='IO19', func=Pin.types.BIDIR)  # ADC2_CH8, U1RTS, USB_D-
    esp32 += Pin(num='14', name='IO20', func=Pin.types.BIDIR)  # ADC2_CH9, U1CTS, USB_D+
    esp32 += Pin(num='15', name='IO3', func=Pin.types.BIDIR)   # ADC1_CH2, TOUCH3
    esp32 += Pin(num='16', name='IO46', func=Pin.types.INPUT)  # 只能输入
    esp32 += Pin(num='17', name='IO9', func=Pin.types.BIDIR)   # ADC1_CH8, FSPIHD
    esp32 += Pin(num='18', name='IO10', func=Pin.types.BIDIR)  # ADC1_CH9, FSPICS0
    esp32 += Pin(num='19', name='IO11', func=Pin.types.BIDIR)  # ADC2_CH0, FSPID
    esp32 += Pin(num='20', name='IO12', func=Pin.types.BIDIR)  # ADC2_CH1, FSPICLK
    
    # GPIO 引脚 (右侧 21-39)
    esp32 += Pin(num='21', name='IO13', func=Pin.types.BIDIR)  # ADC2_CH2, FSPIQ
    esp32 += Pin(num='22', name='IO14', func=Pin.types.BIDIR)  # ADC2_CH3, FSPIWP
    esp32 += Pin(num='23', name='IO21', func=Pin.types.BIDIR)  # RTC_GPIO21
    esp32 += Pin(num='24', name='IO47', func=Pin.types.BIDIR)  # SPICLK_P
    esp32 += Pin(num='25', name='IO48', func=Pin.types.BIDIR)  # SPICLK_N
    esp32 += Pin(num='26', name='IO45', func=Pin.types.BIDIR)  # GPIO45
    esp32 += Pin(num='27', name='IO0', func=Pin.types.BIDIR)   # BOOT/Strapping
    
    # ⚠️ 引脚28-30已被内部PSRAM占用，N16R8型号不可用
    esp32 += Pin(num='28', name='IO35_PSRAM', func=Pin.types.NOCONNECT)  # 连接PSRAM
    esp32 += Pin(num='29', name='IO36_PSRAM', func=Pin.types.NOCONNECT)  # 连接PSRAM
    esp32 += Pin(num='30', name='IO37_PSRAM', func=Pin.types.NOCONNECT)  # 连接PSRAM
    
    esp32 += Pin(num='31', name='IO38', func=Pin.types.BIDIR)  # FSPIWP
    esp32 += Pin(num='32', name='IO39', func=Pin.types.BIDIR)  # MTCK
    esp32 += Pin(num='33', name='IO40', func=Pin.types.BIDIR)  # MTDO
    esp32 += Pin(num='34', name='IO41', func=Pin.types.BIDIR)  # MTDI
    esp32 += Pin(num='35', name='IO42', func=Pin.types.BIDIR)  # MTMS
    esp32 += Pin(num='36', name='RXD0', func=Pin.types.BIDIR)  # GPIO44, U0RXD
    esp32 += Pin(num='37', name='TXD0', func=Pin.types.BIDIR)  # GPIO43, U0TXD
    esp32 += Pin(num='38', name='IO2', func=Pin.types.BIDIR)   # ADC1_CH1, TOUCH2
    esp32 += Pin(num='39', name='IO1', func=Pin.types.BIDIR)   # ADC1_CH0, TOUCH1
    
    return esp32

# 导出模板
ESP32_S3_WROOM = create_esp32_s3_wroom()
