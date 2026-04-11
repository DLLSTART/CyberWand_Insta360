# 魔杖 STL 导出脚本

## 功能
使用 OpenSCAD 命令行将 `wand_reverse_v1.scad` 渲染为 STL 文件

## 使用方法

### 方式 1：直接导出（推荐）
```powershell
# 打开 "C:\Program Files\OpenSCAD\openscad.exe"
& "C:\Program Files\OpenSCAD\openscad.exe" -o wand_reverse_v1.stl wand_reverse_v1.scad
```

### 方式 2：高质量导出
```powershell
& "C:\Program Files\OpenSCAD\openscad.exe" -o wand_reverse_v1.stl --render --preview=throwaway wand_reverse_v1.scad
```

### 方式 3：使用脚本自动导出
```powershell
python export_wand_stl.py
```

## 输出文件
- `wand_reverse_v1.stl` - 3D 打印用 STL 文件
- 预计文件大小：约 5-10 MB
- 预计打印时间：8-12 小时（FDM, 0.2mm 层高）
- 预计材料用量：约 40-50g PLA

## 参数调整

如需调整魔杖尺寸，编辑 `wand_reverse_v1.scad` 中的参数：

```openscad
total_length = 350;    // 总长度 mm
handle_dia = 22;       // 手柄直径 mm
tip_dia = 5;           // 顶端直径 mm

nodes = [
    [35,  26, 22],   // 节点 1
    [80,  23, 19],   // 节点 2
    ...
];
```

## 3D 打印建议

### FDM 打印（经济）
- 材料：PLA 棕色/深棕色
- 层高：0.15-0.2mm
- 填充：15-20%
- 支撑：需要（悬空节点）
- 成本：¥30-50

### SLA 打印（高细节）
- 材料：灰色树脂 + 手工上色
- 层高：0.05mm
- 成本：¥80-120

### 后处理
1. 去除支撑
2. 打磨（400→800→1200 目砂纸）
3. 上色（丙烯颜料/模型漆）
4. 保护漆（消光/半光）

---

**创建时间**: 2026-04-06  
**创建人**: 太子
