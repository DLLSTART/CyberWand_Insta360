"""
USBLC6-2SC6 USB ESD 保护芯片 SKiDL 描述
型号：USBLC6-2SC6
制造商：STMicroelectronics
封装：SOT-23-6
描述：超低电容 USB ESD 保护阵列
    - 保护2路数据线 + 1路VBUS
    - ESD 保护等级: IEC 61000-4-2 ±30kV 空气放电 / ±25kV 接触放电
    - 数据线电容: 0.4pF (典型)
    - 工作电压: 5V
    - 钳位电压: 10V@1A
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_usblc6_2sc6():
    """创建 USBLC6-2SC6 ESD 保护芯片"""

    esd = Part(
        name='USBLC6-2SC6',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_TO_SOT_SMD:SOT-23-6',
        description='USB ESD Protection, SOT-23-6, 0.4pF, IEC61000-4-2 Level 4'
    )

    # 引脚定义 (SOT-23-6)
    esd += Pin(num='1', name='IO1_1', func=Pin.types.PASSIVE)   # I/O 1 输入
    esd += Pin(num='2', name='GND', func=Pin.types.PWRIN)       # 地
    esd += Pin(num='3', name='IO2_1', func=Pin.types.PASSIVE)   # I/O 2 输入
    esd += Pin(num='4', name='IO2_2', func=Pin.types.PASSIVE)   # I/O 2 输出
    esd += Pin(num='5', name='VBUS', func=Pin.types.PWRIN)      # VBUS (5V)
    esd += Pin(num='6', name='IO1_2', func=Pin.types.PASSIVE)   # I/O 1 输出

    return esd

# 导出模板
USBLC6_2SC6 = create_usblc6_2sc6()
