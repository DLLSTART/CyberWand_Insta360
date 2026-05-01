# Enclosure 外壳设计

CyberWand 的 3D 外壳模型与文档。

## 📁 文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `elder_wand_design.md` | 设计文档 | **葡萄藤雕花魔杖** 3D 参数化设计 v4.0（2026-05-01）|
| `elder_wand.scad` | OpenSCAD 模型 | 参数化模型，分 4 段导出 STL |
| `render_preview.scad` | 渲染脚本 | 7 种预览视图（横放/轴测/剖切/特写/爆炸）|
| `魔杖上手图.png` | reference 图像 | **当前主用 reference**（葡萄藤雕花魔杖手持照）|
| `old_wand.png` | reference 图像 | 旧版老魔杖参考（v2/v3 时代）|
| `cyberwand.png` | 旧版渲染 | v0 历史渲染图 |
| `output/` | 渲染输出 | PNG 预览图（已加 .gitignore）|

## 🧙 当前主用方案：v4.0 葡萄藤雕花魔杖

按 `魔杖上手图.png` 上手图比例还原的纤细优雅魔杖：

- **D Pommel 铜帽**（z=0..8）: 多段曲线车削黄铜帽，**独立可旋盖**（M6 螺纹访问电池）
- **A 手柄**（z=14..104, 90 mm）: Φ34→Φ32 微锥圆柱木柄，内含 Φ31×82 mm 电子腔
- **上铜环**（z=104..111）: Φ34→Φ24 双梯形仿铜环
- **B 鳞纹带 + 雕花结**（z=111..151）: 5 道 V 形深槽 + 椭球雕花结（赤道 6 凸点）
- **C 螺旋杖身**（z=156..330, 174 mm）: 双股螺旋藤蔓 1.8 圈，Φ16→Φ4 锥度
- **锥尖**（z=330..360）: Φ4→Φ1.2 平滑锥
- **PCB+电池竖向叠放**: 电池靠 pommel（重心下移），PCB 靠杖身（接口易访问）

### 杖身宽度优化（vs v3）

| 维度 | v3 老魔杖 | v4 葡萄藤雕花 | 减少量 |
|---|---|---|---|
| 最大杖身 X-Y 直径 | Φ44（C1 簇外延） | Φ34（手柄） | **−23 %** |
| 杖身长度 | 380 mm | 360 mm | −5 % |
| 装配段 | 4 | 4 | − |

### 一键导出 STL（4 段分件打印）

```bash
# 段 D — Pommel 铜帽（独立旋盖，建议黄铜色 PLA）
openscad -o wand_pommel.stl   -D 'PART="D"' elder_wand.scad

# 段 A — Handle 手柄（含电子腔，z = 14 ~ 104 mm，90 mm）
openscad -o wand_handle.stl   -D 'PART="A"' elder_wand.scad

# 段 B — Decor 雕花段（含上铜环+鳞纹带+雕花结，52 mm）
openscad -o wand_decor.stl    -D 'PART="B"' elder_wand.scad

# 段 C — Spiral Shaft + Tip 螺旋杖身 + 锥尖（210 mm）
openscad -o wand_shaft.stl    -D 'PART="C"' elder_wand.scad

# 完整预览（含 PCB / 电池占位透视）
openscad -o wand_preview.stl  -D 'PART="PREVIEW"' elder_wand.scad
```

### 关键参数（详见 `elder_wand_design.md`）

| 参数 | 值 |
|------|----|
| 总长 | 360 mm |
| 手柄长度 | 90 mm（成年男性手心抓握） |
| 手柄外径 | Φ34 → Φ32 微锥 |
| 杖身根 / 梢 | Φ16 → Φ4 |
| 锥尖 | Φ1.2 mm |
| 螺旋圈数 | 1.8 圈 / 174 mm |
| 螺旋藤蔓数 | 2 道（双股） |
| 电子腔 | Φ31 × 82 mm |
| PCB+电池摆放 | **沿杖轴竖向叠放** |
| 段数 | 4 段（D/A/B/C） |
| 推荐材料 | 木丝 PLA（A/B/C）+ 黄铜色 PLA（D） |
| 总耗材 | ≈48 g |
| 总打印时长 | ≈6 h |

## 🔑 PCB 沿杖轴竟向摆放（v4 关键创新）

```
   z=98 ──── 腔顶
   ┌──────┐
   │ PCB  │ z=62..97（35 mm）  ← 接口 / 按键 / LED 在 PCB 端
   │ 25mm │
   └──────┘
   z=58 ── 4 mm 间隔（连接器）
   ┌──────┐
   │ Batt │ z=18..58（40 mm）  ← 重电池靠 pommel，配重佳
   │ 30mm │
   └──────┘
   z=16 ── 腔底（pommel 螺孔上）
```

## 📐 修改设计

所有尺寸集中在 `elder_wand.scad` 顶部 CONFIG 区，调整后重跑导出命令即可：

```scad
total_length     = 360;   // 总长 mm
handle_dia_bot   = 34;    // 手柄底径
handle_dia_top   = 32;    // 手柄顶径
spiral_root_dia  = 16;    // 螺旋杖身根
spiral_tip_dia   = 4;     // 螺旋杖身梢
tip_dia          = 1.2;   // 杖尖
spiral_turns     = 1.8;   // 螺旋圈数
spiral_vines     = 2;     // 藤蔓数（双股 / 单股）
vine_height      = 1.4;   // 藤蔓凸出高度
cavity_id        = 31;    // 电子腔内径
cavity_len       = 82;    // 电子腔长度
```

段位 z 边界 (`pommel_z_top`, `handle_z_top`, `band_z_top`, `knot_z_top`, `collar_z_top`, `spiral_z_top`) 也都暴露在 CONFIG 区。

## 🎨 渲染预览

```bash
# 7 种视图一次性渲染（自动并行）
openscad -o output/wand_horizontal.png --imgsize=1600,400 \
  --camera=180,0,0,90,0,0,520 -D 'VIEW="HORIZONTAL"' render_preview.scad

# 其他 VIEW: ISO / SECTION / EXPLODED / POMMEL_CLOSEUP / BAND_CLOSEUP / TIP_CLOSEUP
```

---

**最后更新**: 2026-05-01  
**当前版本**: 葡萄藤雕花魔杖 v4.0（按 `魔杖上手图.png` 比例 + PCB 竖向摆放）  
**历史版本**: v3.1 老魔杖工业美学 / v2.0 老魔杖高保真 / v1.0 初版
