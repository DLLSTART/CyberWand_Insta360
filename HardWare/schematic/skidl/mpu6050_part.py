"""
MPU6050 6轴运动传感器 SKiDL 描述
型号：MPU-6050
制造商：InvenSense (TDK)
封装：QFN-24 (4x4mm, 0.5mm间距)
描述：3轴陀螺仪 + 3轴加速度计，I2C接口

★ 引脚定义严格按照 MPU-6050 Product Specification Rev 3.4 (QFN-24):
  Pin 1:  CLKIN   - 外部参考时钟输入 (不用时接GND)
  Pin 2-5:  NC    - 未内部连接
  Pin 6:  AUX_DA  - 辅助I2C数据 (连外部传感器用, 可不接)
  Pin 7:  AUX_CL  - 辅助I2C时钟
  Pin 8:  VLOGIC  - 数字I/O参考电压 (1.71V~VDD, 通常接VDD)
  Pin 9:  AD0     - I2C从地址最低位 (GND=0x68, VDD=0x69)
  Pin 10: REGOUT  - 内部稳压器输出 (★必须接100nF到GND)
  Pin 11: FSYNC   - 帧同步输入 (不用时接GND)
  Pin 12: INT     - 中断输出 (开漏/推挽可配置)
  Pin 13: VDD     - 主电源 (2.375V~3.46V)
  Pin 14-17: NC   - 未内部连接
  Pin 18: GND     - 地
  Pin 19: RESV    - 保留 (不连接)
  Pin 20: CPOUT   - 电荷泵输出 (★必须接2.2nF到GND)
  Pin 21-22: NC   - 未内部连接
  Pin 23: SCL     - I2C时钟
  Pin 24: SDA     - I2C数据
  EP:     GND     - 散热焊盘 (连接GND)
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_mpu6050():
    """创建 MPU6050 传感器 (引脚严格按QFN-24数据手册)"""

    mpu = Part(
        name='MPU-6050',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm',
        description='MPU6050 6-axis IMU, QFN-24'
    )

    # 电源引脚
    mpu += Pin(num='13', name='VDD',    func=Pin.types.PWRIN)   # 主电源
    mpu += Pin(num='18', name='GND',    func=Pin.types.PWRIN)   # 地
    mpu += Pin(num='8',  name='VLOGIC', func=Pin.types.PWRIN)   # 数字I/O参考电压

    # I2C 接口
    mpu += Pin(num='24', name='SDA',    func=Pin.types.BIDIR)   # I2C数据
    mpu += Pin(num='23', name='SCL',    func=Pin.types.INPUT)   # I2C时钟

    # 地址选择和中断
    mpu += Pin(num='9',  name='AD0',    func=Pin.types.INPUT)   # 地址LSB
    mpu += Pin(num='12', name='INT',    func=Pin.types.OUTPUT)  # 中断

    # 辅助 I2C (可选, 连接外部磁力计等)
    mpu += Pin(num='6',  name='AUX_DA', func=Pin.types.BIDIR)
    mpu += Pin(num='7',  name='AUX_CL', func=Pin.types.BIDIR)

    # 时钟和同步
    mpu += Pin(num='1',  name='CLKIN',  func=Pin.types.INPUT)   # ★ 不用时必须接GND
    mpu += Pin(num='11', name='FSYNC',  func=Pin.types.INPUT)   # ★ 不用时必须接GND

    # 内部稳压/电荷泵 (★ 必须外接电容!)
    mpu += Pin(num='20', name='CPOUT',  func=Pin.types.PASSIVE) # ★ 接2.2nF到GND
    mpu += Pin(num='10', name='REGOUT', func=Pin.types.PASSIVE) # ★ 接100nF到GND

    # 保留/不连接
    mpu += Pin(num='19', name='RESV',   func=Pin.types.NOCONNECT)

    return mpu

# 导出模板
MPU6050 = create_mpu6050()
