"""
USB Type-C 母座 SKiDL 描述
型号：USB Type-C 24引脚母座
接口：USB 2.0
支持：正反插，最大3A电流
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_usb_type_c():
    """创建 USB Type-C 母座"""
    
    usb = Part(
        name='USB_C_Receptacle_USB2.0',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='J',
        footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
        description='USB Type-C Receptacle'
    )
    
    # VBUS 引脚（A4, B4）
    usb += Pin(num='A4', name='VBUS_A4', func=Pin.types.PWRIN)
    usb += Pin(num='B4', name='VBUS_B4', func=Pin.types.PWRIN)
    
    # CC 引脚（配置通道）
    usb += Pin(num='A5', name='CC1', func=Pin.types.BIDIR)
    usb += Pin(num='B5', name='CC2', func=Pin.types.BIDIR)
    
    # USB 数据引脚
    usb += Pin(num='A6', name='DP1', func=Pin.types.BIDIR)
    usb += Pin(num='A7', name='DN1', func=Pin.types.BIDIR)
    usb += Pin(num='B6', name='DP2', func=Pin.types.BIDIR)
    usb += Pin(num='B7', name='DN2', func=Pin.types.BIDIR)
    
    # SBU 引脚（辅助信号）
    usb += Pin(num='A8', name='SBU1', func=Pin.types.BIDIR)
    usb += Pin(num='B8', name='SBU2', func=Pin.types.BIDIR)
    
    # GND 引脚
    usb += Pin(num='A1', name='GND_A1', func=Pin.types.PWRIN)
    usb += Pin(num='B1', name='GND_B1', func=Pin.types.PWRIN)
    usb += Pin(num='A12', name='GND_A12', func=Pin.types.PWRIN)
    usb += Pin(num='B12', name='GND_B12', func=Pin.types.PWRIN)
    
    # 金属外壳
    usb += Pin(num='S1', name='SHIELD', func=Pin.types.PASSIVE)
    
    return usb

# 导出模板
USB_TYPE_C = create_usb_type_c()
