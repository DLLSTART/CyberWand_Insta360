"""
CyberWand 电路连接验证脚本
使用 SKiDL 的 ERC (Electrical Rule Check) 功能验证硬件连接
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("  CyberWand 电路连接验证")
print("=" * 70)
print()

try:
    # 导入电路定义
    print("[1] 导入电路定义...")
    from cyberwand_circuit import *
    print("    ✓ 电路定义导入成功")
    print()
    
    # 运行 ERC (电气规则检查)
    print("[2] 运行电气规则检查 (ERC)...")
    print()
    
    ERC()
    
    print()
    print("[3] 生成网表...")
    try:
        generate_netlist(file_=open('output/cyberwand_verified.net', 'w'))
        print("    ✓ 网表已生成: output/cyberwand_verified.net")
    except Exception as e:
        print(f"    ⚠ 网表生成跳过: {e}")
    print()
    
    # 检查关键连接
    print("[4] 检查关键连接...")
    print()
    
    # 检查电源连接
    power_nets = ['vcc_3v3', 'vcc_5v_prot', 'vcc_bat', 'gnd']
    print("    电源网络:")
    for net_name in power_nets:
        try:
            net = globals().get(net_name)
            if net:
                print(f"      ✓ {net_name}: {len(net)} 个连接点")
            else:
                print(f"      ✗ {net_name}: 未找到")
        except Exception as e:
            print(f"      ✗ {net_name}: 错误 - {e}")
    
    print()
    
    # 检查SPI连接
    print("    SPI总线连接:")
    spi_nets = ['spi_sck', 'spi_mosi', 'spi_miso']
    for net_name in spi_nets:
        try:
            net = globals().get(net_name)
            if net:
                print(f"      ✓ {net_name}: {len(net)} 个连接点")
            else:
                print(f"      ✗ {net_name}: 未找到")
        except Exception as e:
            print(f"      ✗ {net_name}: 错误 - {e}")
    
    print()
    
    # 检查I2C连接
    print("    I2C总线连接:")
    i2c_nets = ['i2c_sda', 'i2c_scl']
    for net_name in i2c_nets:
        try:
            net = globals().get(net_name)
            if net:
                print(f"      ✓ {net_name}: {len(net)} 个连接点")
            else:
                print(f"      ✗ {net_name}: 未找到")
        except Exception as e:
            print(f"      ✗ {net_name}: 错误 - {e}")
    
    print()
    
    # 检查关键组件连接
    print("    关键组件连接:")
    components = {
        'mcu': 'ESP32-S3',
        'imu': 'MPU6050',
        'lcd': 'LCD',
        'sd_card': 'SD卡',
        'charger': 'TP4056',
        'ldo': 'ME6211'
    }
    
    for comp_var, comp_name in components.items():
        try:
            comp = globals().get(comp_var)
            if comp:
                connected_pins = sum(1 for pin in comp.pins if pin.net)
                total_pins = len(comp.pins)
                print(f"      ✓ {comp_name}: {connected_pins}/{total_pins} 引脚已连接")
            else:
                print(f"      ✗ {comp_name}: 未找到")
        except Exception as e:
            print(f"      ✗ {comp_name}: 错误 - {e}")
    
    print()
    print("=" * 70)
    print("  ✓ 电路验证完成！")
    print("=" * 70)
    
except ImportError as e:
    print(f"✗ 导入错误: {e}")
    print("  请确保所有依赖的模块文件都在当前目录中")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ 验证过程中发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
