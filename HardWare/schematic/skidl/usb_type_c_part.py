"""
USB Type-C 母座 SKiDL 描述
型号：TYPE-C 16PIN 2MD(073)
制造商：深圳市首韩科技有限公司 (SHOU HAN)
封装：14引脚 SMD（左侧12引脚 + 右侧2引脚SHELL）
接口：USB 2.0
支持：正反插，最大3A电流
工作温度：-25°C ~ +85°C

★ 引脚定义（根据实际封装图）
  左侧12个引脚（从上到下）：
    Pin 1: GND
    Pin 2: VBUS
    Pin 3: SBU2
    Pin 4: CC1
    Pin 5: DN2
    Pin 6: DP1
    Pin 7: DN1
    Pin 8: DP2
    Pin 9: SBU1
    Pin 10: CC2
    Pin 11: VBUS
    Pin 12: GND
  
  右侧2个引脚（从上到下）：
    Pin 13: SHELL
    Pin 14: SHELL
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_usb_type_c():
    """创建 USB Type-C 14引脚母座 (TYPE-C 16PIN 2MD(073))"""
    
    usb = Part(
        name='USB_C_Receptacle_USB2.0',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='J',
        footprint='Connector_USB:USB_C_Receptacle_16PIN_2MD',
        description='USB Type-C 16PIN Receptacle, SHOU HAN TYPE-C 16PIN 2MD(073)'
    )
    
    # ★ 左侧12个引脚（从上到下）
    usb += Pin(num='1', name='GND1', func=Pin.types.PWRIN)        # Pin 1: GND
    usb += Pin(num='2', name='VBUS1', func=Pin.types.PWRIN)       # Pin 2: VBUS
    usb += Pin(num='3', name='SBU2', func=Pin.types.BIDIR)        # Pin 3: SBU2 (辅助信号)
    usb += Pin(num='4', name='CC1', func=Pin.types.BIDIR)         # Pin 4: CC1 (配置通道1)
    usb += Pin(num='5', name='DN2', func=Pin.types.BIDIR)         # Pin 5: DN2 (D-, B侧)
    usb += Pin(num='6', name='DP1', func=Pin.types.BIDIR)         # Pin 6: DP1 (D+, A侧)
    usb += Pin(num='7', name='DN1', func=Pin.types.BIDIR)         # Pin 7: DN1 (D-, A侧)
    usb += Pin(num='8', name='DP2', func=Pin.types.BIDIR)         # Pin 8: DP2 (D+, B侧)
    usb += Pin(num='9', name='SBU1', func=Pin.types.BIDIR)        # Pin 9: SBU1 (辅助信号)
    usb += Pin(num='10', name='CC2', func=Pin.types.BIDIR)        # Pin 10: CC2 (配置通道2)
    usb += Pin(num='11', name='VBUS2', func=Pin.types.PWRIN)      # Pin 11: VBUS
    usb += Pin(num='12', name='GND2', func=Pin.types.PWRIN)      # Pin 12: GND
    
    # ★ 右侧2个SHELL引脚
    usb += Pin(num='13', name='SHELL1', func=Pin.types.PASSIVE)   # Pin 13: SHELL (金属外壳)
    usb += Pin(num='14', name='SHELL2', func=Pin.types.PASSIVE)   # Pin 14: SHELL (金属外壳)
    
    return usb

# 导出模板
USB_TYPE_C = create_usb_type_c()
