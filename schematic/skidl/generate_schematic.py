#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KiCad 9.0 原理图生成器
从网表文件生成.kicad_sch原理图文件
"""

import re
import uuid
from datetime import datetime
from pathlib import Path


class NetlistParser:
    """网表解析器"""
    
    def __init__(self, netlist_path):
        self.netlist_path = netlist_path
        self.components = []
        self.nets = []
        
    def parse(self):
        """解析网表文件"""
        print(f"[1/5] 读取网表文件: {self.netlist_path}")
        
        with open(self.netlist_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析元件
        self._parse_components(content)
        
        # 解析网络连接
        self._parse_nets(content)
        
        print(f"      找到 {len(self.components)} 个元件")
        print(f"      找到 {len(self.nets)} 个网络")
        
    def _parse_components(self, content):
        """解析元件信息"""
        # 查找components块 - 不依赖libparts
        components_match = re.search(r'\(components\s+(.*?)(?=\n\s*\(nets|\n\s*\(libraries|\Z)', content, re.DOTALL)
        if not components_match:
            print("      [WARN] 未找到components块")
            return
        
        components_block = components_match.group(1)
        
        # 分割每个comp块 - 使用更精确的匹配
        # 找到所有 (comp 开始位置
        comp_starts = [m.start() for m in re.finditer(r'\(comp\s', components_block)]
        
        for i, start in enumerate(comp_starts):
            # 找到对应的结束位置
            if i < len(comp_starts) - 1:
                comp_text = components_block[start:comp_starts[i+1]]
            else:
                comp_text = components_block[start:]
            
            # 提取字段
            ref = self._extract_field(comp_text, 'ref')
            value = self._extract_field(comp_text, 'value')
            footprint = self._extract_field(comp_text, 'footprint')
            
            if not ref:
                continue
            
            component = {
                'ref': ref,
                'value': value or 'Unknown',
                'footprint': footprint or '',
                'lib': 'Device',  # 默认库
                'part': 'R',  # 默认器件
                'pins': []
            }
            
            # 提取库信息
            libsource = re.search(r'\(libsource\s+(.*?)\n\s*\)', comp_text, re.DOTALL)
            if libsource:
                lib_text = libsource.group(1)
                lib_name = self._extract_field(lib_text, 'lib')
                part_name = self._extract_field(lib_text, 'part')
                if lib_name:
                    component['lib'] = lib_name
                if part_name:
                    component['part'] = part_name
            
            self.components.append(component)
    
    def _parse_nets(self, content):
        """解析网络连接"""
        # 查找nets块
        nets_match = re.search(r'\(nets\s+(.*?)\n\s*\)\s*\Z', content, re.DOTALL)
        if not nets_match:
            print("      [WARN] 未找到nets块")
            return
        
        nets_block = nets_match.group(1)
        
        # 匹配网络块：(net (code "X") (name "NetName") ... )
        net_pattern = r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\n\s*\(net\s|\Z)'
        
        for match in re.finditer(net_pattern, nets_block, re.DOTALL):
            net_code = match.group(1)
            net_name = match.group(2)
            nodes_text = match.group(3)
            
            # 解析节点：(node (ref "R1") (pin "1") ...)
            node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
            nodes = []
            
            for node_match in re.finditer(node_pattern, nodes_text):
                nodes.append({
                    'ref': node_match.group(1),
                    'pin': node_match.group(2)
                })
            
            if len(nodes) >= 2:  # 至少2个节点才形成连接
                self.nets.append({
                    'code': net_code,
                    'name': net_name,
                    'nodes': nodes
                })
    
    def _extract_field(self, text, field_name):
        """提取字段值"""
        pattern = rf'\({field_name}\s+"([^"]*)"\)'
        match = re.search(pattern, text)
        return match.group(1) if match else ''


class SchematicGenerator:
    """原理图生成器"""
    
    def __init__(self, components, nets, output_path):
        self.components = components
        self.nets = nets
        self.output_path = output_path
        
        # 布局参数
        self.grid_size = 25.4  # 1英寸 = 25.4mm
        self.spacing_x = 50.8  # 2英寸
        self.spacing_y = 50.8  # 2英寸
        self.start_x = 50.8
        self.start_y = 50.8
        self.cols = 6  # 每行6个元件
        
        # UUID映射
        self.component_uuids = {}
        
    def generate(self):
        """生成原理图文件"""
        print(f"\n[2/5] 计算元件布局...")
        self._calculate_positions()
        
        print(f"[3/5] 生成UUID...")
        self._generate_uuids()
        
        print(f"[4/5] 生成原理图内容...")
        schematic_content = self._build_schematic()
        
        print(f"[5/5] 写入文件: {self.output_path}")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(schematic_content)
        
        print(f"\n[OK] 原理图生成成功!")
        print(f"      文件: {self.output_path}")
        print(f"      元件数: {len(self.components)}")
        print(f"      连接数: {len(self.nets)}")
        
    def _calculate_positions(self):
        """计算元件位置（网格布局）"""
        for i, comp in enumerate(self.components):
            row = i // self.cols
            col = i % self.cols
            
            comp['x'] = self.start_x + col * self.spacing_x
            comp['y'] = self.start_y + row * self.spacing_y
            
    def _generate_uuids(self):
        """为每个元件生成UUID"""
        for comp in self.components:
            comp['uuid'] = str(uuid.uuid4())
            self.component_uuids[comp['ref']] = comp['uuid']
    
    def _build_schematic(self):
        """构建原理图文件内容"""
        lines = []
        
        # 文件头
        lines.append('(kicad_sch')
        lines.append('  (version 20231120)')
        lines.append('  (generator "skidl_schematic_generator")')
        lines.append('  (generator_version "1.0")')
        lines.append('')
        
        # UUID
        lines.append(f'  (uuid "{uuid.uuid4()}")')
        lines.append('')
        
        # 纸张设置
        lines.append('  (paper "A3")')
        lines.append('')
        
        # 库符号（需要声明使用的库）
        lines.append('  (lib_symbols')
        self._add_lib_symbols(lines)
        lines.append('  )')
        lines.append('')
        
        # 总线别名（可选）
        lines.append('  (bus_alias)')
        lines.append('')
        
        # 图形项
        lines.append('  (junction)')
        lines.append('')
        
        lines.append('  (no_connect)')
        lines.append('')
        
        # 连接线
        self._add_wires(lines)
        lines.append('')
        
        # 元件符号实例
        for comp in self.components:
            self._add_symbol_instance(lines, comp)
        
        # Sheet实例（顶层sheet）
        lines.append('  (sheet_instances')
        lines.append('    (path "/"')
        lines.append('      (page "1")')
        lines.append('    )')
        lines.append('  )')
        lines.append('')
        
        lines.append(')')
        
        return '\n'.join(lines)
    
    def _add_lib_symbols(self, lines):
        """添加库符号声明"""
        # 收集所有使用的库和符号
        lib_parts = set()
        for comp in self.components:
            lib_parts.add((comp['lib'], comp['part']))
        
        for lib, part in sorted(lib_parts):
            symbol_name = f"{lib}:{part}"
            lines.append(f'    (symbol "{symbol_name}"')
            lines.append('      (pin_names (offset 0.254))')
            lines.append('      (exclude_from_sim no)')
            lines.append('      (in_bom yes)')
            lines.append('      (on_board yes)')
            lines.append('      (property "Reference" "U"')
            lines.append('        (at 0 2.54 0)')
            lines.append('        (effects')
            lines.append('          (font (size 1.27 1.27))')
            lines.append('        )')
            lines.append('      )')
            lines.append('      (property "Value" ""')
            lines.append('        (at 0 0 0)')
            lines.append('        (effects')
            lines.append('          (font (size 1.27 1.27))')
            lines.append('        )')
            lines.append('      )')
            lines.append('      (property "Footprint" ""')
            lines.append('        (at 0 0 0)')
            lines.append('        (effects')
            lines.append('          (font (size 1.27 1.27))')
            lines.append('          (hide yes)')
            lines.append('        )')
            lines.append('      )')
            lines.append('      (symbol "' + f"{lib}:{part}_0_1" + '"')
            lines.append('        (rectangle')
            lines.append('          (start -5.08 5.08)')
            lines.append('          (end 5.08 -5.08)')
            lines.append('          (stroke')
            lines.append('            (width 0.254)')
            lines.append('            (type default)')
            lines.append('          )')
            lines.append('          (fill')
            lines.append('            (type background)')
            lines.append('          )')
            lines.append('        )')
            lines.append('      )')
            lines.append('    )')
    
    def _add_wires(self, lines):
        """添加连接线"""
        # 简化处理：为每个网络添加注释
        lines.append('  (wire)')
        for net in self.nets:
            lines.append(f'  ; Net: {net["name"]} (Nodes: {len(net["nodes"])})')
    
    def _add_symbol_instance(self, lines, comp):
        """添加元件符号实例"""
        symbol_name = f"{comp['lib']}:{comp['part']}"
        
        lines.append(f'  (symbol')
        lines.append(f'    (lib_id "{symbol_name}")')
        lines.append(f'    (at {comp["x"]:.4f} {comp["y"]:.4f} 0)')
        lines.append('    (unit 1)')
        lines.append('    (exclude_from_sim no)')
        lines.append('    (in_bom yes)')
        lines.append('    (on_board yes)')
        lines.append('    (dnp no)')
        lines.append(f'    (uuid "{comp["uuid"]}")')
        
        # 属性
        lines.append(f'    (property "Reference" "{comp["ref"]}"')
        lines.append(f'      (at {comp["x"]:.4f} {comp["y"] - 7.62:.4f} 0)')
        lines.append('      (effects')
        lines.append('        (font (size 1.27 1.27))')
        lines.append('      )')
        lines.append('    )')
        
        lines.append(f'    (property "Value" "{comp["value"]}"')
        lines.append(f'      (at {comp["x"]:.4f} {comp["y"] + 7.62:.4f} 0)')
        lines.append('      (effects')
        lines.append('        (font (size 1.27 1.27))')
        lines.append('      )')
        lines.append('    )')
        
        lines.append(f'    (property "Footprint" "{comp["footprint"]}"')
        lines.append(f'      (at {comp["x"]:.4f} {comp["y"]:.4f} 0)')
        lines.append('      (effects')
        lines.append('        (font (size 1.27 1.27))')
        lines.append('        (hide yes)')
        lines.append('      )')
        lines.append('    )')
        
        # 引脚连接（简化）
        lines.append('    (pin "1"')
        lines.append(f'      (uuid "{uuid.uuid4()}")')
        lines.append('    )')
        
        lines.append('    (instances')
        lines.append('      (project "cyberwand"')
        lines.append('        (path "/"')
        lines.append(f'          (reference "{comp["ref"]}")')
        lines.append('          (unit 1)')
        lines.append('        )')
        lines.append('      )')
        lines.append('    )')
        lines.append('  )')


def main():
    """主函数"""
    import sys
    import io
    
    # 设置输出编码为UTF-8
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("KiCad 9.0 原理图生成器")
    print("从SKiDL网表生成.kicad_sch文件")
    print("=" * 60)
    print()
    
    # 文件路径
    script_dir = Path(__file__).parent
    netlist_path = script_dir / 'output' / 'cyberwand_netlist.net'
    output_path = script_dir.parent / 'hardware' / 'cyberwand.kicad_sch'
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 检查网表文件
    if not netlist_path.exists():
        print(f"[ERROR] 网表文件不存在: {netlist_path}")
        print(f"        请先运行: python cyberwand_circuit.py")
        return 1
    
    try:
        # 解析网表
        parser = NetlistParser(netlist_path)
        parser.parse()
        
        # 生成原理图
        generator = SchematicGenerator(
            parser.components,
            parser.nets,
            output_path
        )
        generator.generate()
        
        print()
        print("=" * 60)
        print("完成!")
        print("=" * 60)
        print()
        print("接下来的步骤:")
        print("1. 打开KiCad主界面")
        print("2. 文件 -> 打开项目")
        print(f"3. 选择: {output_path.parent}")
        print("4. 双击打开原理图文件")
        print("5. 手动调整元件位置（元件会堆叠在网格上）")
        print()
        print("提示: 在原理图编辑器中可以使用:")
        print("  - 按 M 键移动元件")
        print("  - 按 R 键旋转元件")
        print("  - 按 G 键拖动元件（保持连线）")
        print("  - 工具 -> 排列符号 (自动排列)")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
