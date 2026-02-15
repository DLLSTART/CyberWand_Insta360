"""
MicroSD 卡座 SKiDL 描述
型号：DM3AT-SF-PEJM5
制造商：Hirose
接口：SPI
支持：MicroSD 卡（最大32GB）

★ 引脚定义（根据实际封装图，14引脚）
  左侧引脚（Pin1-8，从上到下）：
    Pin1: DAT2, Pin2: CD/DAT3, Pin3: CMD, Pin4: VDD
    Pin5: CLK, Pin6: VSS, Pin7: DAT0, Pin8: DAT1
  
  右侧引脚（Pin9-14，从上到下）：
    Pin9: SW_B, Pin10: (未标注), Pin11: SW_A, Pin12-14: (未标注)
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_microsd_socket():
    """创建 MicroSD 卡座（DM3AT-SF-PEJM5，14引脚）"""
    
    sd = Part(
        name='MicroSD_Socket',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='J',
        footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',
        description='MicroSD Socket DM3AT-SF-PEJM5 with SPI, 14-pin'
    )
    
    # ★ 左侧引脚（Pin1-8，从上到下）
    sd += Pin(num='1', name='DAT2', func=Pin.types.BIDIR)       # Pin1: DAT2
    sd += Pin(num='2', name='CD_DAT3', func=Pin.types.BIDIR)    # Pin2: CD/DAT3 (卡检测/数据3)
    sd += Pin(num='3', name='CMD', func=Pin.types.INPUT)        # Pin3: CMD (SPI模式下用作CS)
    sd += Pin(num='4', name='VDD', func=Pin.types.PWRIN)        # Pin4: VDD (电源)
    sd += Pin(num='5', name='CLK', func=Pin.types.INPUT)        # Pin5: CLK (SPI时钟)
    sd += Pin(num='6', name='VSS', func=Pin.types.PWRIN)        # Pin6: VSS (地)
    sd += Pin(num='7', name='DAT0', func=Pin.types.TRISTATE)    # Pin7: DAT0 (SPI MISO)
    sd += Pin(num='8', name='DAT1', func=Pin.types.BIDIR)        # Pin8: DAT1
    
    # ★ 右侧引脚（Pin9-14，从上到下）
    sd += Pin(num='9', name='SW_B', func=Pin.types.PASSIVE)     # Pin9: SW_B (开关B)
    sd += Pin(num='10', name='NC1', func=Pin.types.NOCONNECT)   # Pin10: 未标注
    sd += Pin(num='11', name='SW_A', func=Pin.types.PASSIVE)    # Pin11: SW_A (开关A)
    sd += Pin(num='12', name='NC2', func=Pin.types.NOCONNECT)   # Pin12: 未标注
    sd += Pin(num='13', name='NC3', func=Pin.types.NOCONNECT)    # Pin13: 未标注
    sd += Pin(num='14', name='NC4', func=Pin.types.NOCONNECT)   # Pin14: 未标注
    
    # 为了向后兼容，添加别名映射到SPI模式
    # SPI模式下：CMD→CS, CLK→SCK, DAT0→MISO, DAT1→MOSI (但DAT1在SPI模式下通常不用)
    
    return sd

# 导出模板
MICROSD_SOCKET = create_microsd_socket()
