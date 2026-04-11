"""
PTC 自恢复保险丝 SKiDL 描述
型号：MF-MSMF075-2 (或兼容型号)
制造商：Bourns
封装：SMD 1206
描述：USB VBUS 过流保护

★ v2.3修复: 从500mA升级到750mA
  原因: 充电500mA + LED空闲13mA + 指示灯3mA = 516mA > 500mA旧保持电流
  新规格:
    - 保持电流 Ih = 750mA (充电+所有外设正常工作)
    - 触发电流 It = 1.5A
    - 最大电压: 13.2V
    - 最大电阻: 0.10Ω (比500mA型号更低内阻)
    - 工作温度: -40C ~ +85C
    - USB 2.0规范允许500mA, USB Type-C可协商最高3A
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_ptc_fuse():
    """创建 PTC 自恢复保险丝 750mA"""

    fuse = Part(
        name='PTC_Fuse',
        value='750mA',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='F',
        footprint='Fuse:Fuse_1206_3216Metric',
        description='PTC Resettable Fuse 750mA/13.2V, 1206'
    )

    fuse += Pin(num='1', name='1', func=Pin.types.PASSIVE)
    fuse += Pin(num='2', name='2', func=Pin.types.PASSIVE)

    return fuse

# 导出模板
PTC_FUSE_500MA = create_ptc_fuse()  # 保持导出名兼容
