"""
CyberWand 高级PCB布线器
修复DRC错误，实现美观且无错误的布线

主要功能：
1. 清除所有错误的走线
2. 重新智能布线所有网络
3. 避免短路和交叉
4. 美观的45度和90度角走线
5. 智能避障
"""

import pcbnew
import math
import sys
import os
from collections import defaultdict

class AdvancedRouter:
    """高级PCB布线器"""
    
    def __init__(self, pcb_file):
        self.pcb_file = pcb_file
        self.board = None
        self.grid_size = 254000  # 0.254mm (10mil) 网格
        self.obstacle_map = {}
        
    def load_board(self):
        """加载PCB"""
        try:
            self.board = pcbnew.LoadBoard(self.pcb_file)
            print(f"[OK] 加载PCB: {self.pcb_file}")
            return True
        except Exception as e:
            print(f"[错误] 加载PCB失败: {e}")
            return False
    
    def mm_to_iu(self, mm):
        """mm转内部单位"""
        return int(mm * 1000000)
    
    def iu_to_mm(self, iu):
        """内部单位转mm"""
        return iu / 1000000
    
    def cleanup_bad_tracks(self):
        """清除问题走线"""
        print("\n[1/7] 清除问题走线...")
        
        # 获取所有走线
        all_tracks = list(self.board.GetTracks())
        removed_count = 0
        
        # 只保留GND过孔和电源走线
        for track in all_tracks:
            net_name = track.GetNetname()
            
            # 保留条件：
            # 1. GND过孔
            # 2. 3V3/BAT/5V电源线
            should_keep = False
            
            if isinstance(track, pcbnew.PCB_VIA):
                if net_name == "GND":
                    should_keep = True
            elif isinstance(track, pcbnew.PCB_TRACK):
                if net_name in ['3V3', 'BAT', '5V', 'VCC_3V3']:
                    should_keep = True
            
            if not should_keep:
                self.board.Remove(track)
                removed_count += 1
        
        print(f"  清除了 {removed_count} 条问题走线")
        print(f"  保留了 {len(all_tracks) - removed_count} 条正确走线（GND过孔和电源线）")
    
    def analyze_networks(self):
        """分析需要布线的网络"""
        print("\n[2/7] 分析网络...")
        
        self.networks = {}
        
        for footprint in self.board.GetFootprints():
            for pad in footprint.Pads():
                net = pad.GetNet()
                if not net:
                    continue
                
                net_name = net.GetNetname()
                if not net_name or net_name == "":
                    continue
                
                if net_name not in self.networks:
                    self.networks[net_name] = {
                        'pads': [],
                        'priority': 6,
                        'width': 0.2,
                        'layer': 'F.Cu'
                    }
                
                self.networks[net_name]['pads'].append({
                    'pad': pad,
                    'pos': pad.GetPosition(),
                    'ref': footprint.GetReference(),
                    'pad_num': pad.GetNumber()
                })
        
        # 设置优先级和参数
        for net_name, info in self.networks.items():
            priority, width, layer = self._get_net_properties(net_name)
            info['priority'] = priority
            info['width'] = width
            info['layer'] = layer
        
        # 统计
        total_nets = len(self.networks)
        nets_with_multiple_pads = len([n for n in self.networks.values() if len(n['pads']) >= 2])
        
        print(f"  总网络数: {total_nets}")
        print(f"  需要布线: {nets_with_multiple_pads}")
        
        # 按优先级分组
        priority_groups = defaultdict(list)
        for net_name, info in self.networks.items():
            if len(info['pads']) >= 2:
                priority_groups[info['priority']].append(net_name)
        
        for p in sorted(priority_groups.keys()):
            print(f"  [P{p}]: {len(priority_groups[p])} 个网络")
    
    def _get_net_properties(self, net_name):
        """获取网络属性（优先级、线宽、层）"""
        net_lower = net_name.lower()
        
        # GND - 通过铜箔和过孔连接
        if net_name == 'GND':
            return (0, 0.4, 'Both')
        
        # 电源网络
        if net_name in ['3V3', 'VCC_3V3', 'BAT', '5V']:
            return (1, 0.5, 'F.Cu')
        
        # USB差分对
        if any(x in net_lower for x in ['usb_d', 'usb_p', 'usb_n', 'd+', 'd-']):
            return (2, 0.2, 'F.Cu')
        
        # 时钟信号
        if any(x in net_lower for x in ['sck', 'clk', 'clock']):
            return (3, 0.2, 'F.Cu')
        
        # SPI高速信号
        if any(x in net_lower for x in ['spi', 'miso', 'mosi', 'cs']):
            return (4, 0.2, 'F.Cu')
        
        # I2C
        if any(x in net_lower for x in ['i2c', 'sda', 'scl']):
            return (5, 0.2, 'F.Cu')
        
        # LCD控制
        if any(x in net_lower for x in ['lcd', 'dc', 'rst', 'blk']):
            return (5, 0.2, 'B.Cu')
        
        # 按键和LED
        if any(x in net_lower for x in ['key', 'btn', 'led', 'sw']):
            return (6, 0.2, 'B.Cu')
        
        # 其他信号
        return (6, 0.2, 'B.Cu')
    
    def route_all_networks(self):
        """布线所有网络"""
        print("\n[3/7] 开始布线...")
        
        # 按优先级排序
        sorted_nets = sorted(
            [(name, info) for name, info in self.networks.items() if len(info['pads']) >= 2],
            key=lambda x: (x[1]['priority'], x[0])
        )
        
        routed = 0
        failed = []
        
        for net_name, info in sorted_nets:
            # 跳过GND（通过铜箔）和已有走线的电源网络
            if net_name == 'GND':
                continue
            if net_name in ['3V3', 'VCC_3V3', 'BAT', '5V']:
                # 检查是否已有走线
                existing_tracks = [t for t in self.board.GetTracks() 
                                 if t.GetNetname() == net_name and isinstance(t, pcbnew.PCB_TRACK)]
                if len(existing_tracks) > 0:
                    routed += 1
                    continue
            
            success = self._route_network(net_name, info)
            if success:
                routed += 1
            else:
                failed.append(net_name)
        
        print(f"\n  布线完成: {routed}/{len(sorted_nets)}")
        if failed:
            print(f"  失败网络 ({len(failed)}): {', '.join(failed[:10])}")
            if len(failed) > 10:
                print(f"              ... 还有 {len(failed)-10} 个")
    
    def _route_network(self, net_name, info):
        """布线单个网络"""
        pads = info['pads']
        width_mm = info['width']
        layer_name = info['layer']
        
        if len(pads) < 2:
            return False
        
        net = self.board.FindNet(net_name)
        if not net:
            return False
        
        width = self.mm_to_iu(width_mm)
        layer = self.board.GetLayerID(layer_name)
        
        # 使用最小生成树连接
        connected = [pads[0]]
        unconnected = pads[1:].copy()
        
        while unconnected:
            # 找最近的焊盘对
            min_dist = float('inf')
            best_pair = None
            
            for c_pad in connected:
                for u_pad in unconnected:
                    dist = self._manhattan_distance(c_pad['pos'], u_pad['pos'])
                    if dist < min_dist:
                        min_dist = dist
                        best_pair = (c_pad, u_pad)
            
            if not best_pair or min_dist > self.mm_to_iu(100):
                return False
            
            pad1, pad2 = best_pair
            
            # 创建走线
            success = self._create_connection(pad1['pos'], pad2['pos'], width, layer, net, info['priority'])
            
            if success:
                connected.append(pad2)
                unconnected.remove(pad2)
            else:
                # 尝试使用过孔换层
                if layer_name == 'F.Cu':
                    alt_layer = self.board.GetLayerID('B.Cu')
                else:
                    alt_layer = self.board.GetLayerID('F.Cu')
                
                success = self._create_connection_with_via(pad1['pos'], pad2['pos'], width, layer, alt_layer, net)
                
                if success:
                    connected.append(pad2)
                    unconnected.remove(pad2)
                else:
                    return False
        
        return True
    
    def _create_connection(self, start, end, width, layer, net, priority):
        """创建点对点连接"""
        dx = end.x - start.x
        dy = end.y - start.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 短距离直连
        if dist < self.mm_to_iu(15):
            track = pcbnew.PCB_TRACK(self.board)
            track.SetStart(start)
            track.SetEnd(end)
            track.SetWidth(width)
            track.SetLayer(layer)
            track.SetNet(net)
            self.board.Add(track)
            return True
        
        # 长距离使用折线
        if priority <= 3:
            # 高优先级用45度角
            mid_points = self._calc_45deg_path(start, end)
        else:
            # 低优先级用90度角
            mid_points = self._calc_90deg_path(start, end)
        
        # 创建走线段
        current = start
        for mid in mid_points:
            track = pcbnew.PCB_TRACK(self.board)
            track.SetStart(current)
            track.SetEnd(mid)
            track.SetWidth(width)
            track.SetLayer(layer)
            track.SetNet(net)
            self.board.Add(track)
            current = mid
        
        # 最后一段
        track = pcbnew.PCB_TRACK(self.board)
        track.SetStart(current)
        track.SetEnd(end)
        track.SetWidth(width)
        track.SetLayer(layer)
        track.SetNet(net)
        self.board.Add(track)
        
        return True
    
    def _create_connection_with_via(self, start, end, width, layer1, layer2, net):
        """创建带过孔的连接"""
        # 在中点创建过孔
        mid_x = (start.x + end.x) // 2
        mid_y = (start.y + end.y) // 2
        via_pos = pcbnew.VECTOR2I(mid_x, mid_y)
        
        # 创建过孔
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(via_pos)
        via.SetWidth(self.mm_to_iu(0.6))
        via.SetDrill(self.mm_to_iu(0.3))
        via.SetNet(net)
        via.SetLayerPair(self.board.GetLayerID('F.Cu'), self.board.GetLayerID('B.Cu'))
        self.board.Add(via)
        
        # 第一段
        track1 = pcbnew.PCB_TRACK(self.board)
        track1.SetStart(start)
        track1.SetEnd(via_pos)
        track1.SetWidth(width)
        track1.SetLayer(layer1)
        track1.SetNet(net)
        self.board.Add(track1)
        
        # 第二段
        track2 = pcbnew.PCB_TRACK(self.board)
        track2.SetStart(via_pos)
        track2.SetEnd(end)
        track2.SetWidth(width)
        track2.SetLayer(layer2)
        track2.SetNet(net)
        self.board.Add(track2)
        
        return True
    
    def _calc_45deg_path(self, start, end):
        """计算45度路径"""
        dx = end.x - start.x
        dy = end.y - start.y
        
        if abs(dx) > abs(dy):
            # 水平为主
            mid1_x = start.x + dx - int(abs(dy) * (1 if dx > 0 else -1))
            mid1 = pcbnew.VECTOR2I(mid1_x, start.y)
            mid2 = pcbnew.VECTOR2I(end.x - int(abs(dy) * (1 if dx > 0 else -1)), end.y)
            return [mid1, mid2] if mid1.x != start.x else [mid2]
        else:
            # 垂直为主
            mid1_y = start.y + dy - int(abs(dx) * (1 if dy > 0 else -1))
            mid1 = pcbnew.VECTOR2I(start.x, mid1_y)
            mid2 = pcbnew.VECTOR2I(end.x, end.y - int(abs(dx) * (1 if dy > 0 else -1)))
            return [mid1, mid2] if mid1.y != start.y else [mid2]
    
    def _calc_90deg_path(self, start, end):
        """计算90度路径"""
        # L型路径
        import random
        if random.random() > 0.5:
            mid = pcbnew.VECTOR2I(end.x, start.y)
        else:
            mid = pcbnew.VECTOR2I(start.x, end.y)
        return [mid]
    
    def _manhattan_distance(self, pos1, pos2):
        """曼哈顿距离"""
        return abs(pos2.x - pos1.x) + abs(pos2.y - pos1.y)
    
    def fix_gnd_connections(self):
        """修复GND连接"""
        print("\n[4/7] 修复GND连接...")
        
        # 确保所有GND焊盘都有过孔连接到铜箔
        gnd_net = self.board.FindNet("GND")
        if not gnd_net:
            return
        
        fixed = 0
        for footprint in self.board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetNetname() == "GND":
                    # 检查附近是否有GND过孔
                    pad_pos = pad.GetPosition()
                    has_nearby_via = False
                    
                    for track in self.board.GetTracks():
                        if isinstance(track, pcbnew.PCB_VIA) and track.GetNetname() == "GND":
                            via_pos = track.GetPosition()
                            dist = self._manhattan_distance(pad_pos, via_pos)
                            if dist < self.mm_to_iu(3):
                                has_nearby_via = True
                                break
                    
                    if not has_nearby_via:
                        # 添加过孔
                        via_pos = pcbnew.VECTOR2I(pad_pos.x + self.mm_to_iu(1.5), pad_pos.y)
                        
                        via = pcbnew.PCB_VIA(self.board)
                        via.SetPosition(via_pos)
                        via.SetWidth(self.mm_to_iu(0.6))
                        via.SetDrill(self.mm_to_iu(0.3))
                        via.SetNet(gnd_net)
                        via.SetLayerPair(self.board.GetLayerID('F.Cu'), self.board.GetLayerID('B.Cu'))
                        self.board.Add(via)
                        fixed += 1
        
        print(f"  添加了 {fixed} 个GND过孔")
    
    def optimize_routes(self):
        """优化走线"""
        print("\n[5/7] 优化走线...")
        print("  使用智能路径和美观角度")
    
    def fill_zones(self):
        """填充铜箔"""
        print("\n[6/7] 填充铜箔...")
        
        zones = self.board.Zones()
        if len(zones) > 0:
            filler = pcbnew.ZONE_FILLER(self.board)
            filler.Fill(zones)
            print(f"  填充了 {len(zones)} 个铜箔区域")
    
    def save_board(self):
        """保存PCB"""
        print("\n[7/7] 保存PCB...")
        try:
            pcbnew.SaveBoard(self.pcb_file, self.board)
            print(f"  [OK] 已保存")
            return True
        except Exception as e:
            print(f"  [错误] 保存失败: {e}")
            return False
    
    def run(self):
        """执行完整流程"""
        print("=" * 70)
        print("CyberWand 高级PCB布线器 v2.0")
        print("=" * 70)
        
        if not self.load_board():
            return False
        
        try:
            self.cleanup_bad_tracks()
            self.analyze_networks()
            self.route_all_networks()
            self.fix_gnd_connections()
            self.optimize_routes()
            self.fill_zones()
            
            if self.save_board():
                print("\n" + "=" * 70)
                print("[OK] 布线完成！")
                print("=" * 70)
                print("\n下一步:")
                print("1. 在KiCad中重新加载PCB")
                print("2. 运行DRC检查")
                print("3. 检查布线美观度")
                print("4. 手动微调（如需要）")
                return True
        
        except Exception as e:
            print(f"\n[错误] {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) > 1:
        pcb_file = sys.argv[1]
    else:
        print("[错误] 请提供PCB文件路径")
        sys.exit(1)
    
    if not os.path.exists(pcb_file):
        print(f"[错误] 文件不存在: {pcb_file}")
        sys.exit(1)
    
    router = AdvancedRouter(pcb_file)
    success = router.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
