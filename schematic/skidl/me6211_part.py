"""
ME6211 LDO 稳压芯片 SKiDL 描述
型号：ME6211A33PG-N
制造商：MICRONE
封装：SOT23-3
描述：3.3V LDO稳压器，最大输出电流500mA
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_me6211():
    """创建 ME6211 LDO稳压芯片"""
    
    ldo = Part(
        name='ME6211A33',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_TO_SOT_SMD:SOT-23',
        description='ME6211 3.3V LDO'
    )
    
    # 引脚定义
    ldo += Pin(num='1', name='VIN', func=Pin.types.PWRIN)
    ldo += Pin(num='2', name='GND', func=Pin.types.PWRIN)
    ldo += Pin(num='3', name='VOUT', func=Pin.types.PWROUT)
    
    return ldo

# 导出模板
ME6211 = create_me6211()
