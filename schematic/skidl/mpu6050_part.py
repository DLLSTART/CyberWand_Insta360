"""
MPU6050 6轴运动传感器 SKiDL 描述
型号：MPU6050
制造商：InvenSense (TDK)
封装：QFN-24 (4x4mm)
描述：3轴陀螺仪 + 3轴加速度计，I2C接口
"""

from skidl import Part, Pin, TEMPLATE, SKIDL

def create_mpu6050():
    """创建 MPU6050 传感器"""
    
    mpu = Part(
        name='MPU-6050',
        dest=TEMPLATE,
        tool=SKIDL,
        ref_prefix='U',
        footprint='Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm',
        description='MPU6050 6-axis IMU'
    )
    
    # 电源引脚
    mpu += Pin(num='1', name='VCC', func=Pin.types.PWRIN)
    mpu += Pin(num='18', name='GND', func=Pin.types.PWRIN)
    mpu += Pin(num='13', name='VLOGIC', func=Pin.types.PWRIN)
    
    # I2C 接口
    mpu += Pin(num='23', name='SDA', func=Pin.types.BIDIR)
    mpu += Pin(num='24', name='SCL', func=Pin.types.INPUT)
    
    # 地址选择和中断
    mpu += Pin(num='9', name='AD0', func=Pin.types.INPUT)
    mpu += Pin(num='12', name='INT', func=Pin.types.OUTPUT)
    
    # 辅助 I2C
    mpu += Pin(num='6', name='AUX_DA', func=Pin.types.BIDIR)
    mpu += Pin(num='7', name='AUX_CL', func=Pin.types.BIDIR)
    
    # 时钟引脚
    mpu += Pin(num='20', name='CLKIN', func=Pin.types.INPUT)
    mpu += Pin(num='22', name='CLKOUT', func=Pin.types.OUTPUT)
    
    # 其他引脚
    mpu += Pin(num='3', name='CPOUT', func=Pin.types.PASSIVE)
    mpu += Pin(num='10', name='REGOUT', func=Pin.types.PASSIVE)
    mpu += Pin(num='19', name='RESV', func=Pin.types.NOCONNECT)
    
    return mpu

# 导出模板
MPU6050 = create_mpu6050()
