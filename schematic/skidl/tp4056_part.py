"""
TP4056 锂电池充电管理芯片 SKiDL 描述
型号：TP4056
封装：ESOP-8
描述：单节锂电池线性充电管理，最大充电电流1A
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_tp4056():
    """创建 TP4056 充电管理芯片"""
    
    charger = Part(
        name='TP4056',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
        description='TP4056 Li-Ion Charger'
    )
    
    # 电源引脚
    charger += Pin(num='1', name='VIN', func=Pin.types.PWRIN)
    charger += Pin(num='2', name='GND', func=Pin.types.PWRIN)
    charger += Pin(num='3', name='BAT', func=Pin.types.PWROUT)
    
    # 控制引脚
    charger += Pin(num='4', name='CE', func=Pin.types.INPUT)
    charger += Pin(num='5', name='PROG', func=Pin.types.PASSIVE)
    charger += Pin(num='6', name='RST', func=Pin.types.INPUT)
    
    # 状态指示
    charger += Pin(num='7', name='CHRG', func=Pin.types.OPENCOLL)
    charger += Pin(num='8', name='STDBY', func=Pin.types.OPENCOLL)
    
    return charger

# 导出模板
TP4056 = create_tp4056()
