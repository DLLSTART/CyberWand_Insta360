"""
网表后处理脚本：为元件添加KiCad符号库引用
将 (lib "NO_LIB") 替换为正确的符号库名称
"""

import re
from pathlib import Path

# 元件位号到符号库的映射
SYMBOL_LIB_MAPPING = {
    # 集成电路
    'U1': ('RF_Module', 'ESP32-S3-WROOM-1'),
    'U2': ('Sensor_Motion', 'MPU-6050'),
    'U3': ('Audio', 'DFPlayer_Mini'),
    'U4': ('Battery_Management', 'TP4056'),
    'U5': ('Regulator_Linear', 'AP2112K-3.3'),
    
    # 连接器（使用通用Connector库）
    'J1': ('Connector', 'Conn_01x09'),  # MicroSD卡座
    'J2': ('Connector', 'USB_C_Receptacle_USB2.0'),  # USB Type-C
    
    # 显示和音频（使用通用库）
    'LCD1': ('Connector', 'Conn_01x08'),  # LCD显示屏模块
    'MIC1': ('Connector', 'Conn_01x06'),  # 麦克风模块
    'LS1': ('Device', 'Speaker'),
    
    # 电源
    'BT1': ('Device', 'Battery_Cell'),
    
    # LED
    'D1': ('LED', 'LED_WS2812B'),
    'D2': ('LED', 'LED_WS2812B'),
    'D3': ('LED', 'LED_WS2812B'),
    'D4': ('Device', 'LED'),  # 红色指示LED
    'D5': ('Device', 'LED'),  # 绿色指示LED
    
    # 按键
    'SW1': ('Switch', 'SW_Push'),
    'SW2': ('Switch', 'SW_Push'),
    'SW3': ('Switch', 'SW_Push'),
}

# 根据前缀匹配的默认映射
PREFIX_MAPPING = {
    'R': ('Device', 'R'),       # 电阻
    'C': ('Device', 'C'),       # 电容
}

def get_symbol_lib(ref):
    """根据元件位号获取符号库信息"""
    # 先查找精确匹配
    if ref in SYMBOL_LIB_MAPPING:
        return SYMBOL_LIB_MAPPING[ref]
    
    # 根据前缀匹配
    for prefix, (lib, part) in PREFIX_MAPPING.items():
        if ref.startswith(prefix):
            return (lib, part)
    
    # 未找到，返回 None
    return None

def process_netlist(input_file, output_file=None):
    """处理网表文件，添加符号库引用"""
    if output_file is None:
        output_file = input_file
    
    # 读取网表内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式查找所有元件定义
    # 匹配格式: (comp (ref "XXX") ... (libsource (lib "NO_LIB") (part "YYY")) ...)
    
    def replace_libsource(match):
        """替换 libsource 中的库名"""
        full_match = match.group(0)
        ref = match.group(1)
        old_lib = match.group(2)
        part_name = match.group(3)
        
        # 获取正确的符号库
        symbol_info = get_symbol_lib(ref)
        if symbol_info:
            new_lib, new_part = symbol_info
            # 替换库名和元件名
            new_libsource = f'(libsource\n        (lib "{new_lib}")\n        (part "{new_part}"))'
            # 替换整个 libsource 段
            result = re.sub(
                r'\(libsource\s+\(lib "[^"]+"\)\s+\(part "[^"]+"\)\)',
                new_libsource,
                full_match
            )
            print(f"[OK] {ref}: {old_lib} -> {new_lib}:{new_part}")
            return result
        else:
            print(f"[WARN] {ref}: 未找到符号库映射，保持 {old_lib}")
            return full_match
    
    # 正则表达式匹配元件块
    # 匹配 (comp ... (ref "XXX") ... (libsource (lib "YYY") (part "ZZZ")) ... )
    pattern = r'\(comp\s+\(ref\s+"([^"]+)"\).*?\(libsource\s+\(lib\s+"([^"]+)"\)\s+\(part\s+"([^"]+)"\)\).*?\(tstamps\s+"[^"]+"\)\)'
    
    # 替换所有匹配
    new_content = re.sub(pattern, replace_libsource, content, flags=re.DOTALL)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\n[SUCCESS] 网表处理完成！")
    print(f"输入: {input_file}")
    print(f"输出: {output_file}")
    return output_file

if __name__ == '__main__':
    # 处理网表文件
    input_netlist = Path(__file__).parent / 'output' / 'cyberwand_netlist.net'
    
    if not input_netlist.exists():
        print(f"[ERROR] 找不到网表文件 {input_netlist}")
        exit(1)
    
    print("=" * 60)
    print("开始处理网表，添加KiCad符号库引用...")
    print("=" * 60)
    
    process_netlist(input_netlist)
    
    print("\n现在可以将网表导入到KiCad中，符号将自动识别！")
