"""
603040 聚合物锂电池 SKiDL 描述
型号：603040
标称电压：3.7V
充电电压：4.2V
容量：800mAh
尺寸：30x40x6mm
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_battery_603040():
    """创建 603040 锂电池"""
    
    battery = Part(
        name='Battery_Cell',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='BT',
        footprint='Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal',
        description='603040 Li-Po Battery 800mAh with JST connector'
    )
    
    # 电池引脚
    battery += Pin(num='1', name='+', func=Pin.types.PASSIVE)
    battery += Pin(num='2', name='-', func=Pin.types.PASSIVE)
    
    return battery

# 导出模板
BATTERY_603040 = create_battery_603040()
