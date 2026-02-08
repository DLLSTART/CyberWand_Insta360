"""
PTC 自恢复保险丝 SKiDL 描述
型号：MF-MSMF050-2 (或兼容型号)
制造商：Bourns
封装：SMD 1206
描述：USB VBUS 过流保护
    - 保持电流 Ih = 500mA
    - 触发电流 It = 1.0A
    - 最大电压: 15V
    - 最大电阻: 0.15Ω
    - 触发时间: ~8秒
    - 工作温度: -40°C ~ +85°C
    - RoHS 兼容
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_ptc_fuse():
    """创建 PTC 自恢复保险丝"""

    fuse = Part(
        name='PTC_Fuse',
        value='500mA',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='F',
        footprint='Fuse:Fuse_1206_3216Metric',
        description='PTC Resettable Fuse 500mA/15V, 1206'
    )

    # 2脚被动元件
    fuse += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    fuse += Pin(num='2', name='2', func=Pin.types.PASSIVE)

    return fuse

# 导出模板
PTC_FUSE_500MA = create_ptc_fuse()
