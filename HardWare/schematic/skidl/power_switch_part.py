"""
电源开关 SKiDL 描述
型号：MSK-12C02 (或兼容滑动开关)
封装：SMD 滑动开关
描述：总电源开关，控制电池输出
    - 单刀双掷(SPDT)
    - 额定电流: 0.3A
    - 额定电压: 6V DC
    - 寿命: 10000次
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_power_switch():
    """创建电源滑动开关 (SPDT)"""

    sw = Part(
        name='SW_SPDT',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='SW',
        footprint='Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02',
        description='SPDT Slide Switch for Power Control'
    )

    # 3脚: COM(公共), NO(常开), NC(常闭)
    sw += Pin(num='1', name='COM', func=Pin.types.PASSIVE)   # 公共端 (接电池)
    sw += Pin(num='2', name='NO', func=Pin.types.PASSIVE)    # 常开端 (接系统VIN)
    sw += Pin(num='3', name='NC', func=Pin.types.PASSIVE)    # 常闭端 (可悬空)

    return sw

# 导出模板
POWER_SWITCH = create_power_switch()
