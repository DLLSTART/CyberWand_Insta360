"""
CyberWand PCB 自动布局脚本
使用 KiCad pcbnew Python API 自动化PCB设计

功能：
1. 自动放置元器件到合理位置
2. 设置元器件方向
3. 创建铺铜区域
4. 设置布线规则
5. 添加安装孔

使用方法：
1. 先运行 cyberwand_circuit.py 生成网表
2. 在KiCad中导入网表创建PCB
3. 在KiCad中运行此脚本（工具 -> 外部插件）
   或者在命令行中运行：
   python pcb_auto_layout.py <pcb_file_path>
"""

import pcbnew
import math
import os

# ============================================================
# PCB设计参数配置
# ============================================================

class PCBConfig:
    """PCB设计配置参数"""
    
    # PCB尺寸（单位：mm）
    PCB_WIDTH = 60.0
    PCB_LENGTH = 130.0
    PCB_THICKNESS = 1.6
    
    # 边界距离
    EDGE_MARGIN = 2.0  # 元器件到板边的最小距离
    
    # 元器件布局区域划分（从上到下）
    AREA_TOP = {
        'y_start': 5.0,
        'y_end': 55.0,
        'name': '顶部区域 - LCD显示屏'
    }
    
    AREA_MIDDLE = {
        'y_start': 55.0,
        'y_end': 90.0,
        'name': '中部区域 - 主控和传感器'
    }
    
    AREA_BOTTOM = {
        'y_start': 90.0,
        'y_end': 125.0,
        'name': '底部区域 - 电源和接口'
    }
    
    # 铺铜设置
    COPPER_CLEARANCE = 0.2  # mm
    COPPER_MIN_WIDTH = 0.2  # mm
    
    # 布线规则
    TRACK_WIDTH_POWER = 0.4    # mm - 电源线
    TRACK_WIDTH_SIGNAL = 0.2   # mm - 信号线
    TRACK_WIDTH_USB = 0.2      # mm - USB差分线
    VIA_SIZE = 0.6             # mm - 过孔直径
    VIA_DRILL = 0.3            # mm - 过孔钻孔

# ============================================================
# 元器件位置定义
# ============================================================

class ComponentLayout:
    """元器件布局定义"""
    
    def __init__(self, pcb_width=60.0, pcb_length=130.0):
        self.width = pcb_width
        self.length = pcb_length
        self.center_x = pcb_width / 2.0
        
        # 定义各元器件的目标位置（x, y, rotation）
        # 坐标系：左下角为原点，单位mm，rotation为度数
        
        self.layout = {
            # ==================== 顶部区域：LCD显示屏 ====================
            'LCD1': {
                'x': self.center_x,
                'y': 30.0,
                'rotation': 90,  # 横向放置
                'layer': 'F.Cu',
                'description': 'HS20S010B LCD 2.0寸显示屏'
            },
            
            # ==================== 中部区域：主控和传感器 ====================
            'U1': {  # ESP32-S3主控
                'x': self.center_x,
                'y': 70.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'ESP32-S3-WROOM-1 主控芯片'
            },
            
            'U2': {  # MPU6050传感器
                'x': self.center_x - 15.0,
                'y': 85.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'MPU6050 6轴传感器'
            },
            
            'J1': {  # MicroSD卡座
                'x': 55.0,  # 靠近板边
                'y': 70.0,
                'rotation': 90,
                'layer': 'F.Cu',
                'description': 'MicroSD卡座'
            },
            
            # ==================== 底部区域：电源和接口 ====================
            'J2': {  # USB Type-C接口
                'x': self.center_x,
                'y': 125.0,
                'rotation': 90,
                'layer': 'F.Cu',
                'description': 'USB Type-C接口'
            },
            
            'U4': {  # TP4056充电芯片
                'x': self.center_x - 12.0,
                'y': 110.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'TP4056充电管理'
            },
            
            'U5': {  # ME6211稳压芯片
                'x': self.center_x + 12.0,
                'y': 110.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'ME6211 3.3V稳压'
            },
            
            'BT1': {  # 电池连接器
                'x': self.center_x,
                'y': 100.0,
                'rotation': 0,
                'layer': 'B.Cu',  # 背面
                'description': '603040锂电池连接'
            },
            
            # ==================== 外设模块 ====================
            'U3': {  # DFPlayer Mini
                'x': self.center_x + 15.0,
                'y': 85.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'DFPlayer音频模块'
            },
            
            'MIC1': {  # INMP441麦克风
                'x': 10.0,
                'y': 70.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'INMP441麦克风'
            },
            
            'LS1': {  # 扬声器
                'x': self.center_x,
                'y': 50.0,
                'rotation': 0,
                'layer': 'B.Cu',  # 背面
                'description': '扬声器'
            },
            
            # ==================== LED ====================
            'D1': {  # WS2812B LED1
                'x': 15.0,
                'y': 20.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'RGB LED 1'
            },
            
            'D2': {  # WS2812B LED2
                'x': self.center_x,
                'y': 20.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'RGB LED 2'
            },
            
            'D3': {  # WS2812B LED3
                'x': 45.0,
                'y': 20.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': 'RGB LED 3'
            },
            
            'D4': {  # 充电指示LED红色
                'x': 50.0,
                'y': 115.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': '红色充电指示LED'
            },
            
            'D5': {  # 充电指示LED绿色
                'x': 50.0,
                'y': 110.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': '绿色充满指示LED'
            },
            
            # ==================== 按键 ====================
            'SW1': {  # 模式选择按键
                'x': 8.0,
                'y': 95.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': '模式选择按键'
            },
            
            'SW2': {  # 手势选择按键
                'x': 8.0,
                'y': 85.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': '手势选择按键'
            },
            
            'SW3': {  # 播放确认按键
                'x': 8.0,
                'y': 75.0,
                'rotation': 0,
                'layer': 'F.Cu',
                'description': '播放确认按键'
            },
        }
        
        # 被动元件自动放置在主芯片附近
        self._add_passive_components()
    
    def _add_passive_components(self):
        """自动计算被动元件位置"""
        # 电容和电阻放置在主芯片周围
        
        # ESP32去耦电容
        self.layout['C1'] = {'x': 20.0, 'y': 65.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C2'] = {'x': 22.0, 'y': 65.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C3'] = {'x': 24.0, 'y': 65.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # MPU6050去耦电容
        self.layout['C4'] = {'x': 20.0, 'y': 82.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # LCD去耦电容
        self.layout['C5'] = {'x': 35.0, 'y': 25.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C6'] = {'x': 37.0, 'y': 25.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # LDO电容
        self.layout['C7'] = {'x': 40.0, 'y': 108.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C8'] = {'x': 42.0, 'y': 108.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # USB滤波电容
        self.layout['C9'] = {'x': 35.0, 'y': 120.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # 其他电容
        self.layout['C10'] = {'x': 40.0, 'y': 82.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C11'] = {'x': 42.0, 'y': 82.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['C12'] = {'x': 18.0, 'y': 18.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # 上拉电阻
        self.layout['R1'] = {'x': 26.0, 'y': 65.0, 'rotation': 90, 'layer': 'F.Cu'}  # EN上拉
        self.layout['R2'] = {'x': 18.0, 'y': 88.0, 'rotation': 0, 'layer': 'F.Cu'}   # I2C SDA
        self.layout['R3'] = {'x': 18.0, 'y': 86.0, 'rotation': 0, 'layer': 'F.Cu'}   # I2C SCL
        
        # 按键上拉电阻
        self.layout['R4'] = {'x': 10.0, 'y': 95.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['R5'] = {'x': 10.0, 'y': 85.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['R6'] = {'x': 10.0, 'y': 75.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # Type-C CC电阻
        self.layout['R7'] = {'x': 25.0, 'y': 122.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['R8'] = {'x': 27.0, 'y': 122.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # TP4056 PROG电阻
        self.layout['R9'] = {'x': 22.0, 'y': 108.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # LED限流电阻
        self.layout['R10'] = {'x': 48.0, 'y': 115.0, 'rotation': 0, 'layer': 'F.Cu'}
        self.layout['R11'] = {'x': 48.0, 'y': 110.0, 'rotation': 0, 'layer': 'F.Cu'}
        
        # IO46下拉电阻
        self.layout['R12'] = {'x': 28.0, 'y': 65.0, 'rotation': 90, 'layer': 'F.Cu'}

# ============================================================
# PCB自动布局主类
# ============================================================

class PCBAutoLayout:
    """PCB自动布局处理类"""
    
    def __init__(self, pcb_file_path):
        self.pcb_file_path = pcb_file_path
        self.board = None
        self.config = PCBConfig()
        self.layout = ComponentLayout(self.config.PCB_WIDTH, self.config.PCB_LENGTH)
        
    def load_board(self):
        """加载PCB文件"""
        try:
            self.board = pcbnew.LoadBoard(self.pcb_file_path)
            print(f"✅ 成功加载PCB: {self.pcb_file_path}")
            return True
        except Exception as e:
            print(f"❌ 加载PCB失败: {e}")
            return False
    
    def mm_to_pcbnew(self, mm):
        """转换mm到pcbnew内部单位（纳米）"""
        return int(mm * 1000000)
    
    def place_components(self):
        """自动放置所有元器件"""
        print("\n开始自动放置元器件...")
        placed_count = 0
        
        for footprint in self.board.GetFootprints():
            ref = footprint.GetReference()
            
            if ref in self.layout.layout:
                layout_info = self.layout.layout[ref]
                
                # 设置位置
                x_mm = layout_info['x']
                y_mm = layout_info['y']
                x_pcb = self.mm_to_pcbnew(x_mm)
                y_pcb = self.mm_to_pcbnew(y_mm)
                
                footprint.SetPosition(pcbnew.VECTOR2I(x_pcb, y_pcb))
                
                # 设置旋转角度
                rotation = layout_info['rotation']
                footprint.SetOrientationDegrees(rotation)
                
                # 设置层（正面/背面）
                if layout_info.get('layer') == 'B.Cu':
                    footprint.Flip(footprint.GetPosition(), False)
                
                placed_count += 1
                desc = layout_info.get('description', '')
                print(f"  ✅ {ref:10s} -> ({x_mm:5.1f}, {y_mm:5.1f}) mm, {rotation:3d}° | {desc}")
            else:
                print(f"  ⚠️ {ref:10s} -> 未定义布局位置")
        
        print(f"\n✅ 已放置 {placed_count} 个元器件")
    
    def create_board_outline(self):
        """创建PCB板框"""
        print("\n创建PCB板框...")
        
        # 删除现有板框
        for drawing in self.board.GetDrawings():
            if drawing.GetLayerName() == 'Edge.Cuts':
                self.board.Remove(drawing)
        
        # 创建矩形板框
        width = self.mm_to_pcbnew(self.config.PCB_WIDTH)
        height = self.mm_to_pcbnew(self.config.PCB_LENGTH)
        
        # 板框四个角的坐标
        points = [
            (0, 0),
            (width, 0),
            (width, height),
            (0, height),
            (0, 0)  # 闭合
        ]
        
        edge_layer = self.board.GetLayerID('Edge.Cuts')
        
        for i in range(len(points) - 1):
            line = pcbnew.PCB_SHAPE(self.board)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(pcbnew.VECTOR2I(points[i][0], points[i][1]))
            line.SetEnd(pcbnew.VECTOR2I(points[i+1][0], points[i+1][1]))
            line.SetLayer(edge_layer)
            line.SetWidth(self.mm_to_pcbnew(0.15))
            self.board.Add(line)
        
        print(f"  ✅ 板框尺寸: {self.config.PCB_WIDTH} x {self.config.PCB_LENGTH} mm")
    
    def add_mounting_holes(self):
        """添加安装孔"""
        print("\n添加安装孔...")
        
        hole_diameter = self.mm_to_pcbnew(3.0)  # 3mm钻孔
        margin = self.mm_to_pcbnew(5.0)  # 距离板边5mm
        
        width = self.mm_to_pcbnew(self.config.PCB_WIDTH)
        height = self.mm_to_pcbnew(self.config.PCB_LENGTH)
        
        # 四个角的安装孔位置
        holes = [
            (margin, margin),                    # 左下
            (width - margin, margin),            # 右下
            (margin, height - margin),           # 左上
            (width - margin, height - margin),   # 右上
        ]
        
        for i, (x, y) in enumerate(holes):
            # 创建一个虚拟的footprint来容纳这个pad
            footprint = pcbnew.FOOTPRINT(self.board)
            footprint.SetReference(f"H{i+1}")
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            
            # 创建PAD并添加到footprint
            pad = pcbnew.PAD(footprint)
            pad.SetSize(pcbnew.VECTOR2I(hole_diameter, hole_diameter))
            pad.SetDrillSize(pcbnew.VECTOR2I(hole_diameter, hole_diameter))
            pad.SetPosition(pcbnew.VECTOR2I(x, y))
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)  # 非金属化孔
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            
            footprint.Add(pad)
            self.board.Add(footprint)
            
            print(f"  ✅ H{i+1} 安装孔: ({x/1000000:.1f}, {y/1000000:.1f}) mm")
    
    def create_copper_zones(self):
        """创建铺铜区域"""
        print("\n创建铺铜区域...")
        
        # GND铺铜（正面）
        self._create_zone(
            layer_name='F.Cu',
            net_name='GND',
            priority=1,
            name='GND铺铜（正面）'
        )
        
        # GND铺铜（背面）
        self._create_zone(
            layer_name='B.Cu',
            net_name='GND',
            priority=1,
            name='GND铺铜（背面）'
        )
        
        print("  ✅ 已创建铺铜区域")
    
    def _create_zone(self, layer_name, net_name, priority, name):
        """创建单个铺铜区域"""
        zone = pcbnew.ZONE(self.board)
        
        # 设置层
        layer_id = self.board.GetLayerID(layer_name)
        zone.SetLayer(layer_id)
        
        # 设置网络
        netinfo = self.board.FindNet(net_name)
        if netinfo:
            zone.SetNet(netinfo)
        
        # 设置优先级
        zone.SetAssignedPriority(priority)
        
        # 设置铜箔参数
        zone.SetMinThickness(self.mm_to_pcbnew(self.config.COPPER_MIN_WIDTH))
        zone.SetThermalReliefGap(self.mm_to_pcbnew(self.config.COPPER_CLEARANCE))
        zone.SetThermalReliefSpokeWidth(self.mm_to_pcbnew(0.3))
        
        # 设置铺铜区域边界（整个PCB板）
        margin = self.mm_to_pcbnew(0.5)  # 距离板边0.5mm
        width = self.mm_to_pcbnew(self.config.PCB_WIDTH) - margin * 2
        height = self.mm_to_pcbnew(self.config.PCB_LENGTH) - margin * 2
        
        outline = zone.Outline()
        outline.NewOutline()
        outline.Append(margin, margin)
        outline.Append(margin + width, margin)
        outline.Append(margin + width, margin + height)
        outline.Append(margin, margin + height)
        
        self.board.Add(zone)
        
        print(f"  ✅ {name} @ {layer_name}")
    
    def setup_design_rules(self):
        """设置设计规则"""
        print("\n设置设计规则...")
        
        design_settings = self.board.GetDesignSettings()
        
        # 设置最小走线宽度
        design_settings.m_TrackMinWidth = self.mm_to_pcbnew(self.config.TRACK_WIDTH_SIGNAL)
        
        # 设置过孔尺寸
        design_settings.m_ViasMinSize = self.mm_to_pcbnew(self.config.VIA_SIZE)
        design_settings.m_ViasMinDrill = self.mm_to_pcbnew(self.config.VIA_DRILL)
        
        # 设置最小间距
        design_settings.m_MinClearance = self.mm_to_pcbnew(0.15)
        
        print(f"  ✅ 信号线宽度: {self.config.TRACK_WIDTH_SIGNAL} mm")
        print(f"  ✅ 电源线宽度: {self.config.TRACK_WIDTH_POWER} mm")
        print(f"  ✅ 过孔尺寸: {self.config.VIA_SIZE} mm")
        print(f"  ✅ 过孔钻孔: {self.config.VIA_DRILL} mm")
    
    def add_text_labels(self):
        """添加文本标注"""
        print("\n添加文本标注...")
        
        # 添加项目名称
        self._add_text(
            text="CyberWand",
            x=30.0, y=5.0,
            layer='F.SilkS',
            size=2.0,
            thickness=0.3
        )
        
        # 添加版本信息
        self._add_text(
            text="v1.0",
            x=50.0, y=5.0,
            layer='F.SilkS',
            size=1.5,
            thickness=0.25
        )
        
        print("  ✅ 已添加文本标注")
    
    def _add_text(self, text, x, y, layer, size, thickness):
        """添加单个文本"""
        pcb_text = pcbnew.PCB_TEXT(self.board)
        pcb_text.SetText(text)
        pcb_text.SetPosition(pcbnew.VECTOR2I(
            self.mm_to_pcbnew(x),
            self.mm_to_pcbnew(y)
        ))
        pcb_text.SetLayer(self.board.GetLayerID(layer))
        pcb_text.SetTextSize(pcbnew.VECTOR2I(
            self.mm_to_pcbnew(size),
            self.mm_to_pcbnew(size)
        ))
        pcb_text.SetTextThickness(self.mm_to_pcbnew(thickness))
        self.board.Add(pcb_text)
    
    def save_board(self):
        """保存PCB文件"""
        try:
            pcbnew.SaveBoard(self.pcb_file_path, self.board)
            print(f"\n✅ PCB已保存: {self.pcb_file_path}")
            return True
        except Exception as e:
            print(f"\n❌ 保存PCB失败: {e}")
            return False
    
    def run(self):
        """执行完整的自动布局流程"""
        print("=" * 60)
        print("CyberWand PCB 自动布局工具")
        print("=" * 60)
        
        if not self.load_board():
            return False
        
        try:
            # 1. 创建板框
            self.create_board_outline()
            
            # 2. 自动放置元器件
            self.place_components()
            
            # 3. 添加安装孔
            self.add_mounting_holes()
            
            # 4. 创建铺铜区域
            self.create_copper_zones()
            
            # 5. 设置设计规则
            self.setup_design_rules()
            
            # 6. 添加文本标注
            self.add_text_labels()
            
            # 7. 保存PCB
            if self.save_board():
                print("\n" + "=" * 60)
                print("✅ PCB自动布局完成！")
                print("=" * 60)
                print("\n下一步操作:")
                print("1. 在KiCad中打开PCB文件")
                print("2. 运行DRC检查（工具 -> 设计规则检查）")
                print("3. 运行自动布线（布线 -> 自动布线）或手动布线")
                print("4. 填充铜箔区域（编辑 -> 填充所有铜箔区域）")
                print("5. 生成Gerber文件进行打样")
                return True
            
        except Exception as e:
            print(f"\n❌ 自动布局过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

# ============================================================
# 主程序入口
# ============================================================

def main():
    """主程序"""
    import sys
    
    # 获取PCB文件路径
    if len(sys.argv) > 1:
        pcb_file = sys.argv[1]
    else:
        # 默认路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        pcb_file = os.path.join(project_root, 'HardWare', 'cyberwand.kicad_pcb')
    
    if not os.path.exists(pcb_file):
        print(f"❌ PCB文件不存在: {pcb_file}")
        print("\n请先：")
        print("1. 运行 cyberwand_circuit.py 生成网表")
        print("2. 在KiCad中创建PCB并导入网表")
        print("3. 保存PCB文件")
        print("4. 再运行此脚本")
        return
    
    # 执行自动布局
    layout_tool = PCBAutoLayout(pcb_file)
    layout_tool.run()

if __name__ == '__main__':
    main()
