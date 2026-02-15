"""
TP4056 锂电池充电管理芯片 SKiDL 描述
型号：TP4056 (NanJing Top Power ASIC)
封装：9引脚（8个标准引脚 + 1个EP散热焊盘）
描述：单节锂电池线性充电管理，最大充电电流1A

★ 引脚映射 (根据实际封装图):
  Pin 1: TEMP  - 温度监测 (接NTC热敏电阻，或接GND禁用)
  Pin 2: PROG  - 充电电流设置 (R_PROG到GND, I=1000V/R)
  Pin 3: GND   - 地
  Pin 4: VCC   - 输入电源 (4.0V~8.0V)
  Pin 5: BAT   - 电池连接 (充电输出)
  Pin 6: STDBY# - 充电完成指示 (开漏输出, 低有效)
  Pin 7: CHRG# - 正在充电指示 (开漏输出, 低有效)
  Pin 8: CE    - 芯片使能 (高电平使能)
  Pin 9: EP    - 散热焊盘 (连接到GND)

★ 注意: CHRG#/STDBY#为开漏输出!
  正确LED接法: VCC → R → LED阳极 → LED阴极 → CHRG#/STDBY#引脚
  (开漏低电平时拉电流, LED亮)
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_tp4056():
    """创建 TP4056 充电管理芯片 (9引脚，包括EP)"""

    charger = Part(
        name='TP4056',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
        description='TP4056 Li-Ion Charger, 9-pin (8 pins + EP)'
    )

    charger += Pin(num='1', name='TEMP',  func=Pin.types.INPUT)      # 温度监测
    charger += Pin(num='2', name='PROG',  func=Pin.types.PASSIVE)    # 充电电流设置
    charger += Pin(num='3', name='GND',   func=Pin.types.PWRIN)      # 地
    charger += Pin(num='4', name='VCC',   func=Pin.types.PWRIN)      # 输入电源
    charger += Pin(num='5', name='BAT',   func=Pin.types.PWROUT)     # 电池
    charger += Pin(num='6', name='STDBY', func=Pin.types.OPENCOLL)   # 充满指示(开漏)
    charger += Pin(num='7', name='CHRG',  func=Pin.types.OPENCOLL)   # 充电指示(开漏)
    charger += Pin(num='8', name='CE',    func=Pin.types.INPUT)      # 芯片使能
    charger += Pin(num='9', name='EP',    func=Pin.types.PWRIN)      # 散热焊盘 (连接到GND)

    return charger

# 导出模板
TP4056 = create_tp4056()
