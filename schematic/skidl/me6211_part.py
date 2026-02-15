"""
ME6211 LDO 稳压芯片 SKiDL 描述
型号：ME6211A33M3G-N (SOT-23-3)
制造商：MICRONE (南京微盟)
封装：SOT-23-3
描述：3.3V LDO稳压器，最大输出500mA

★ SOT-23-3 引脚定义 (按数据手册):
  Pin 1: VIN  - 输入电压 (2.0V ~ 6.0V)
  Pin 2: VOUT - 稳压输出 (3.3V)
  Pin 3: VSS  - 地 (GND)

  注意: ME6211A33PG-N 是SOT-89封装, 引脚顺序不同!
        SOT-89: Pin1=VSS, Pin2=VOUT, Pin3=VIN
  本设计使用SOT-23-3 (M3G-N后缀)
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_me6211():
    """创建 ME6211 LDO (SOT-23-3, 引脚按数据手册)"""

    ldo = Part(
        name='ME6211A33',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_TO_SOT_SMD:SOT-23',
        description='ME6211 3.3V/500mA LDO, SOT-23-3'
    )

    # ★ 引脚严格按 ME6211 SOT-23-3 数据手册
    ldo += Pin(num='1', name='VIN',  func=Pin.types.PWRIN)    # Pin1: 输入
    ldo += Pin(num='2', name='VOUT', func=Pin.types.PWROUT)   # Pin2: 输出 (原来错成GND!)
    ldo += Pin(num='3', name='VSS',  func=Pin.types.PWRIN)    # Pin3: 地   (原来错成VOUT!)

    return ldo

# 导出模板
ME6211 = create_me6211()
