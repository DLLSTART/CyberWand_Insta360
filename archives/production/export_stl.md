# CyberWand v21.0 - 批量导出 STL 脚本

## Windows PowerShell 一键导出

```powershell
# 切换到生产目录
cd D:\workspace\CyberWand_Insta360\production

# 导出手柄
echo "导出 handle_v21.stl..."
openscad -o handle_v21.stl handle_v21.scad

# 导出杖身（4 段）
echo "导出 shaft_v21_segment_1.stl..."
openscad -o shaft_v21_segment_1.stl -D segment_num=1 shaft_v21.scad

echo "导出 shaft_v21_segment_2.stl..."
openscad -o shaft_v21_segment_2.stl -D segment_num=2 shaft_v21.scad

echo "导出 shaft_v21_segment_3.stl..."
openscad -o shaft_v21_segment_3.stl -D segment_num=3 shaft_v21.scad

echo "导出 shaft_v21_segment_4.stl..."
openscad -o shaft_v21_segment_4.stl -D segment_num=4 shaft_v21.scad

# 导出杖尖
echo "导出 tip_v21.stl..."
openscad -o tip_v21.stl tip_v21.scad

# 导出按键帽（3 个）
echo "导出 button_cap_v21.stl..."
openscad -o button_cap_v21.stl button_cap_v21.scad

echo "所有 STL 文件导出完成！"
```

## Linux/Mac Bash 一键导出

```bash
#!/bin/bash

cd /path/to/CyberWand_Insta360/production

echo "导出 handle_v21.stl..."
openscad -o handle_v21.stl handle_v21.scad

echo "导出杖身分段..."
for i in 1 2 3 4; do
    openscad -o shaft_v21_segment_$i.stl -D segment_num=$i shaft_v21.scad
done

echo "导出 tip_v21.stl..."
openscad -o tip_v21.stl tip_v21.scad

echo "导出 button_cap_v21.stl..."
openscad -o button_cap_v21.stl button_cap_v21.scad

echo "所有 STL 文件导出完成！"
```

## 导出文件清单

| 文件 | 尺寸 | 打印时间 | 耗材 |
|------|------|---------|------|
| `handle_v21.stl` | Φ22×12mm | 2.5h | 25g |
| `shaft_v21_segment_1.stl` | Φ14-12×84.5mm | 2h | 10g |
| `shaft_v21_segment_2.stl` | Φ12-11×84.5mm | 2h | 10g |
| `shaft_v21_segment_3.stl` | Φ11-9×84.5mm | 2h | 10g |
| `shaft_v21_segment_4.stl` | Φ9-8×84.5mm | 2h | 10g |
| `tip_v21.stl` | Φ10-5×25mm | 0.5h | 5g |
| `button_cap_v21.stl` | Φ8×4mm | 0.3h | 3g |
| **总计** | - | **11.3h** | **73g** |

## 3D 打印服务推荐

### 淘宝代打印（推荐新手）

| 店铺 | 材料 | 价格 | 链接 |
|------|------|------|------|
| **创想三维旗舰店** | PLA | ¥0.15/g | 淘宝搜索 |
| **纵维立方旗舰店** | PLA | ¥0.12/g | 淘宝搜索 |
| **光固化打印** | 树脂 | ¥0.2/g | 高精度 |

**73g PLA 打印成本**：约 ¥15-20（含运费）

### 自有 3D 打印机

```
耗材成本：
├── PLA 线材：¥50/kg × 0.073kg = ¥3.65
├── 电费：¥1/h × 11.3h = ¥11.3
└── 总计：约 ¥15
```

## 下一步

1. ✅ **导出 STL** - 运行上述脚本
2. ⏳ **3D 打印** - 自有打印机或淘宝代打印
3. ⏳ **采购元件** - 按 BOM 表采购
4. ⏳ **组装** - 按组装指南操作
