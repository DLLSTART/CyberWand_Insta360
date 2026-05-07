// ============================================================================
//  CyberWand v5.0 — 葡萄藤雕花魔杖（按真实 PCB DXF 重新适配）
//
//  v5 关键变更（vs v4）：
//    1. PCB 尺寸更新为真实值: 28(W) × 45(H) × 1.6(t) mm  (原假设 25×35 偏小)
//    2. ESP32 模组天线突出板顶 5.73 mm, 增加天线净空区
//    3. 手柄延长 +8 mm (Z_SHIFT) 容纳真实 PCB + 天线净空
//    4. 增加 PCB 卡槽: 沿腔内壁开两道宽 1.8 mm 的滑入槽, PCB 厚度被卡死
//    5. 增加 PCB 底端定位台 (防止 PCB 沿轴向下滑撞电池)
//    6. USB-C 方孔从 pommel 端开 (USB 接口在 PCB 板底, 朝 -Z 方向)
//    7. SW1 / SW2 / LED1 / LED2 按 DXF 实际坐标对齐到手柄壁
//
//  整体节奏 (z 边界全部 +8 mm 平移):
//    [Pommel铜帽] [手柄圆柱+8mm] [上铜环] [鳞纹带] [雕花结] [收颈] [螺旋] [锥尖]
//
//  PCB 几何源: enclosure/DXF_PCB1_*.dxf -> output/pcb_geometry.json
//  外形参考:  enclosure/魔杖上手图.png
//  设计文档:  enclosure/elder_wand_design.md
// ============================================================================

// ====== PCB 几何参数 (源于 DXF, 不要手改; 改 PCB 后重跑提取脚本) ============
// 提取脚本: enclosure/scripts/dxf_extract_pcb.py
// 板框: 28(W) × 45(H) × 1.6(t) mm
// PCB local 坐标: 左下角 (0,0), Y 朝上, 单位 mm
//
// 元件 (从丝印文字推得 中心位置, 单位 mm):
//   U1   ESP32 模组      占据 (5.23..23.23, 0..25.5)  含天线突出板顶 5.73 mm
//   USB1 USB-C 16pin     中心 (9.18,  38.09)  开口朝板底 -Y (= 朝 pommel)
//   SW1  6mm 轻触按键    中心 (~26,    ~5)    板右上, 元件略突出板边
//   SW2  滑动开关        中心 (~5,    ~33)    板左中下
//   LED1 状态 LED         中心 (22.36, 27.36)  板中右
//   LED2 充电指示 LED     中心 (18.81, 42.67)  板底端 (USB 旁)
//   候选定位孔 Φ1.18:    (2.42, 35.35), (2.42, 43.65)  板左侧

pcb_w  = 28;   pcb_h  = 45;   pcb_t = 1.6;     // PCB 板框 + 厚度
pcb_antenna_overhang = 5.73;                    // ESP32 模组突出板顶高度

// 元件中心 (PCB local, x 轴沿短边, y 轴沿长边)
sw1_cx  = 26;     sw1_cy  =  5;                // 6mm 轻触按键
sw2_cx  =  5;     sw2_cy  = 33;                // 滑动开关
led1_cx = 22.36;  led1_cy = 27.36;
led2_cx = 18.81;  led2_cy = 42.67;
usb_cx  =  9.18;  usb_cy  = 38.09;             // USB-C 中心
mount_holes = [[2.42, 35.35], [2.42, 43.65]];  // 定位孔 (Φ1.18 → 用 Φ1.2 销)

// PCB 装入腔体后的方向约定 (wand 坐标系):
//   wand_X = pcb_x - pcb_w/2     (PCB 短边 28 mm 沿 X, 板中线居中)
//   wand_Y = 0                    (PCB 在 X-Z 平面, 厚度方向沿 ±Y)
//   wand_Z = cavity_z_pcb + (pcb_h - pcb_y)
//                                 (PCB 板顶含天线在 +Z, 板底 USB 在 -Z 朝 pommel)

// ====== CONFIG 区 ===========================================================
Z_SHIFT          =   8;     // v5: 手柄拉长 8 mm 容纳真实 45 mm PCB + 天线净空
total_length     = 360 + Z_SHIFT;

// === 段位 z 边界 (装饰段相对距离不变, 全部平移 Z_SHIFT) ===
pommel_z_top     =   8;
handle_z_bot     =  14;
handle_z_top     = 104 + Z_SHIFT;     // 112
ferrule_z_top    = 111 + Z_SHIFT;     // 119
band_z_top       = 129 + Z_SHIFT;     // 137
knot_z_top       = 151 + Z_SHIFT;     // 159
collar_z_top     = 156 + Z_SHIFT;     // 164
spiral_z_top     = 330 + Z_SHIFT;     // 338
//                368                  锥尖

// === 直径参数 (保持 v4) ===
pommel_dia_bot   = 18;
pommel_dia_top   = 24;     // v5.1.6: 22→24, 让顶面容纳 M24 空心螺纹 (Φ20 通孔
                           //   要让偏置 USB 方孔 9×4 @ X=-4.82 穿过, 实测最远点 9.53mm)
handle_dia_bot   = 34;
handle_dia_top   = 32;
ferrule_dia      = 33;
band_dia         = 24;
knot_dia_max     = 28;
collar_dia       = 16;
// v5.1.4: 上铜箍 (top ferrule) — 把原 collar 4mm 直筒改为鼓起的金属环,
// 与下方 ferrule (Φ33 鼓起) 对称, 视觉上"金属箍把木质杖身固定到雕花结",
// 彻底消除 v5.1.3 中 collar 直筒 → spiral 杖身之间的"光圆柱接缝"违和感.
top_ferrule_dia  = 19;
spiral_root_dia  = 16;
spiral_tip_dia   =  4;
tip_dia          =  1.2;

// === 电池实物 (保持) ===
batt_w = 30;   batt_l = 40;   batt_t = 6;       // 603040 锂聚合物

// === 电子腔（圆柱形 + PCB 卡槽，藏在手柄内）================================
//   v5 关键决策: PCB 必须在 pommel 端
//     原因: USB-C 16pin 公头长度仅 7-8 mm. PCB 上 USB-C 母座开口朝 PCB 板底,
//           若 PCB 在手柄上端, USB 母座距 pommel >50 mm, USB 公头根本插不进去.
//     方案: PCB 板底 (含 USB) 朝 pommel, USB 接口体穿过 pommel 中心方孔露出.
//           pommel 因此改为 *永久固定* (粘合 / 一体打印), 不再是可拆旋盖.
//           电池放到 PCB 上方 (~PCB 重 11g vs 电池 8g, 整体重心仍在 PCB 区).
//           ESP32 天线在 PCB 板顶 (朝 +Z), 距腔顶 ~30 mm, 净空充足.
//
//   v5 z 布置:
//     z = -0.5 .. 6.9   USB-C 接口体 (突出 pommel 底 0.5 mm, 体长 7.4 mm)
//     z = 6.9  .. 51.9  PCB 主体 (45 mm)
//     z = 51.9 .. 57.6  ESP32 天线突出区 (5.73 mm, 内含 SMD 模组)
//     z = 51.9 .. 55.9  PCB 顶端缓冲 4 mm (与电池物理隔离)
//     z = 55.9 .. 95.9  锂电池 603040 (40 mm)
//     z = 95.9 .. 100   腔体上端缓冲 / 走线连接器 (4.1 mm)
cavity_id        = 31;
cavity_len       = 94;
// USB 接口体长度 7.4 mm, 让开口端突出 pommel 底 1.5 mm 便于插拔
//   USB 开口端 z = -1.5
//   USB 接口体顶 = PCB 板底 z = -1.5 + 7.4 = 5.9
cavity_z_start   = 6;        // cavity 圆柱底, 紧贴 USB 接口体顶
cavity_z_pcb     = 5.9;      // PCB 板底 z = USB 接口体顶
cavity_z_pcb_top = cavity_z_pcb + pcb_h;       // 50.9, PCB 板顶
cavity_z_ant_top = cavity_z_pcb_top + pcb_antenna_overhang;  // 56.63
cavity_z_batt    = cavity_z_pcb_top + 4;       // 54.9, PCB 板顶上方 4 mm 间隔

// === PCB 卡槽 (沿 wand 轴向开两道, PCB 滑入式装配) ===
//   cavity 半径 15.5, 外壳 handle 段半径 16-17
//   卡槽 = 跨过 PCB 板边 ±14 的小长方腔, X 范围 ±(13..15)
//   卡槽外边 15 < cavity 半径 15.5, 距外壳壁 (≥16) 1.0+ mm 安全
slot_clearance   = 0.20;                // PCB 厚向间隙 (单边 0.1)
pcb_slot_w       = pcb_t + slot_clearance;  // 槽 Y 宽 = 1.8 mm 夹紧 PCB 厚
pcb_slot_depth   = 2.0;                 // 槽 X 长 = 2.0 mm 跨过 PCB 板边 ±1 mm

// === 螺旋雕刻参数（v4.1 单股自然螺旋） ===
spiral_turns     = 2.2;      // 单股需要更多圈数才有"缠绕感"
spiral_vines     = 1;        // 1 道藤蔓（单股自然螺旋）
vine_height      = 2.0;      // 藤蔓凸出于核心的高度（mm，加粗补偿单股）
vine_width_k     = 1.6;      // 藤蔓 2D 椭圆切向拉伸系数（让它像缠绕的"枝"而非"球"）

// === 段间装配 (v5.1.5: 改为 M10 公制螺纹, 打印即连接) =======================
//   设计动机:
//     v5.1.4 之前: Φ8 圆柱榫 + 上下 "铜环" 视觉装饰. 但铜环只是渲染色, 物理上
//                  整段是单一 PLA, 圆柱榫只能靠胶水粘合才锁死, 不算"机械连接".
//     v5.1.5    : 把圆柱榫升级为 M10×1.5 螺纹 (公段顶部凸 5mm 外螺纹, 母段
//                  底部凹 5.2mm 内螺纹). 打印后直接对准、顺时针拧紧 → 螺纹
//                  咬合自锁, 完全不需胶水. 可拆卸维护内部 PCB.
//
//   规格选择 (M10×1.5):
//     直径 10mm — 在 B-C 接缝处 collar_dia=16 主体内, 留 (16-10)/2=3mm 壁厚, 安全
//     节距 1.5mm — 粗牙易拧、对 FDM 打印精度宽容 (较细的 M10×1 易堵层粘连)
//     长度 5mm   — ≈3.3 圈, 抗拉力 PLA 极限 >3000 N ≈ 300 kg, 足够魔杖挥动场景
//     单边 0.30mm 公差 — 配合 0.2mm 层高 / 0.4mm 喷嘴的 FDM 打印
joint_dia        = 10;       // M10 公制螺纹
joint_pitch      = 1.5;      // M10×1.5 粗牙节距
joint_len        = 5;        // 螺纹啮合长度 5 mm

// === D-A 接缝: M24×1 空心螺纹 (v5.1.6: 替代旧 pd_tenon 嵌套榫 + 胶水) =======
//   设计要点:
//     1) 中央 Φ20 通孔 -- 让偏置的 USB-C 接口体 (9×4mm @ X=-4.82) 穿过 pommel
//        实测 USB 方孔 4 角离杖中心最远 9.53mm < Φ20 通孔半径 10mm, 完全包容
//     2) 啮合长度 4mm = 节距 1mm × 4 整圈, 拧到底时 A 段相对 D 旋转 1440° = 0°
//        起始角度 = 终止角度, 用户对齐 SW1 朝向 → 套入 → 顺拧 4 圈到底, 不会错位
//     3) M24×1 细牙在 pommel 顶径 Φ24 内, 凸柱壁厚 (22.8-20)/2 = 1.4mm 安全
//        齿深 0.6mm vs 0.4mm 喷嘴 = 1.5 倍喷嘴宽度, FDM 可清晰打印
da_thread_d      = 24;       // M24 公制螺纹大径
da_thread_p      = 1;        // 节距 1mm (细牙)
da_thread_h      = 4;        // 啮合长度 = 4 整圈, 起止同相位
da_thread_id     = 20;       // 中央通孔 Φ20 (容纳偏置 USB 9×4, 离心最远 9.53mm)
//   PCB 卡槽顶端 45° 引导斜面参数
pcb_slot_chamfer_h = 1.0;    // 入口倒角高度 (顶端 1mm 渐扩)
pcb_slot_chamfer_w = 1.0;    // 倒角四周扩张量
// v5.1.3 删除: 按键 O 圈坑 (凹井设计已自带防尘, 不需 O 圈)

// === v5.1.3 平滑握持 + 凹陷式按键 (彻底重设计 v5.1.2 凸台/防滑纹) =========
//   设计原则: 手柄外表面 100% 光滑圆柱, 不允许任何凸起 (含防滑纹/凸台/定位环)
//             所有功能件 (SW1/SW2/LED) 改成 *从外表面凹下去*
//             外壳强度通过 *内部局部加厚* 维持 (cavity 内壁向 +Y 反凸 1.5 mm)
//
//   (a) 内部加厚岛 wall_thicken_inward:
//       从 cavity 内壁 (r=15.5) 向 +Y 方向再加 1.5 mm 实体, 局部内壁 r=14
//       外壳总壁厚 = 17 (外) - 14 (内) = 3.0 mm
//       不影响 PCB (PCB 板表面 y=0.8, 距加厚后内壁 y=14 还有 13.2 mm)
//       不影响电池 (电池 z=56..96, 加厚岛 z<60 完全错开)
//
//   (b) SW1 凹井 sw1_press_well:
//       外表面 (y=17) 凹下 1.0 mm 的 Φ12 圆形井, 井底 y=16
//       井底再开 Φ5 透通孔 (穿到 PCB 表面 y=0.8) 容纳按键导柱主柱
//       用户拇指自然伸入 1mm 深井按下 → 凸缘下沉 0.4 mm → SW1 触发
//       井底实壁厚 = 16 - 14 = 2.0 mm 安全
//
//   (c) SW2 滑槽 sw2_slide_recess:
//       外表面凹下 0.6 mm 的 4×12 mm 长方形浅槽 (拨杆操作面)
//       槽底再开 4×10 mm 透通孔露出拨杆
//       槽底实壁厚 = (17-0.6) - 14 = 2.4 mm 安全
//
//   (d) LED 凹孔 led_well:
//       外表面凹下 0.8 mm 的 Φ4 圆坑 (扩散光晕, 比 v5.1.2 的 Φ2.5 大 60%)
//       中心 Φ2 透通孔传光到 PCB LED
//       坑底实壁厚 = (17-0.8) - 14 = 2.2 mm 安全
//
//   (e) 删除全部 v5.1.2 凸起特征:
//       - wall_bosses (4 个外凸椭圆岛)            → 删
//       - grip_grooves_cut (8 道防滑纵向凹槽)     → 删 (用户要求平滑)
//       - sw1_locator_ring (Φ8/Φ9 定位环)        → 删 (凹井本身有定位感)
//       - led1_halo (6 道扇形扩散环)              → 删 (凹井+大圆坑有扩散)

// 内部加厚岛参数 (覆盖全部 SW1/SW2/LED1/LED2 区域 + 边缘融合)
thicken_inward_t = 1.5;       // 反凸厚度 (mm), 让局部壁厚从 1.5 增到 3.0
thicken_inward_z0 = 5.0;      // 加厚区起始 z (覆盖 LED2 z=8.4 到 SW1 z=10.9)
thicken_inward_z1 = 60.0;     // 加厚区终止 z (远离电池 z=56)

// === v5.1 交互结构参数 ============================================
//   按键 SW1: 独立按键导柱 (v5.1.3 凸缘改 Φ10×0.6 大薄盘, 沉入凹井)
//             凸缘尺寸在 part_button_pin 模块内部定义 (cap_dia/cap_t)
btn_pin_dia      = 4.6;      // 按键导柱体直径 (穿过外壁透通孔, 间隙 0.4)
btn_pin_clearance = 0.4;     // 外壳孔比导柱大 0.4 (Φ5 vs Φ4.6)
//   导柱总长 = 外壁厚 + (外壁内表面 → SW1 按键帽顶端距离) + 0.5 预压
//   稍后用计算函数动态算

//   滑动开关 SW2 操作槽
sw2_slot_x       = 4.0;      // 沿 PCB X 方向的槽宽 (拨杆 1.5mm + 余量)
sw2_slot_z       = 10.0;     // 沿 wand Z 方向的槽长 (拨动行程 + 余量)

// v5.1.3 删除: LED 凹坑参数 (改由 led_well_d/dep 控制, 在 led_well 模块定义)

//   电池仓 4 道纵向限位筋
batt_rib_w       = 1.5;      // 筋宽 (沿 cavity 切向)
batt_rib_h       = 1.5;      // 筋径向高度 (从 cavity 内壁向轴心凸出)

//   PCB 底端定位台 (避开 USB 接口区)
pcb_seat_t       = 1.0;      // 定位台厚度 (沿 Z)
pcb_seat_x_skip  = 12.0;     // X 中心避让 USB 接口 ±半宽

// === v5.1.7 PCB 工装销 (锁定第 6 自由度: +Z 反弹) ============================
// 利用 PCB 上现有的 Φ1.18 工厂定位孔 (PCB 2.42, 35.35 → wand X=-11.58, Z=15.55)
// 在 A handle 外壁 -Y 侧打一个 Φ1.3 mm 通孔贯穿到 PCB 平面之上.
// 装配时 PCB 滑入到位 → 用户从外面插入一根 Φ1.2 mm × 19 mm PLA 销 (独立打印, F 段)
// 销穿过外壳壁 → PCB Φ1.18 定位孔 → 销头 Φ3 凸缘嵌入外壳 Φ3.2 浅井齐平
// 锁定后 PCB 完全无法 +Z 反弹, 6 自由度 100% 锁死, 仍可通过拔销维护.
//
// 美观: 销头 Φ3 装饰圆点嵌入外壳齐平, 仅在 -Y 一侧, 远离按键面 (+Y), 视觉影响极小
pcb_pin_x        = -11.58;   // PCB 定位孔 1 在 wand X (= 2.42 - pcb_w/2)
pcb_pin_z        =  15.55;   // PCB 定位孔 1 在 wand Z (= cavity_z_pcb + (pcb_h - 35.35))
pcb_pin_dia      =  1.2;     // 销主体直径
pcb_pin_hole_dia =  1.3;     // 外壳通孔直径 (单边 0.05 间隙)
pcb_pin_cap_dia  =  3.0;     // 销头装饰圆点直径
pcb_pin_well_dia =  3.2;     // 外壳浅井直径 (容纳凸缘)
pcb_pin_cap_t    =  0.5;     // 销头凸缘厚度
pcb_pin_well_d   =  0.6;     // 外壳浅井深度 (= 凸缘厚 + 0.1 沉入)
pcb_pin_len      = 19.0;     // 销总长 (从外壁井底到 PCB +Y 上方)

// v5.1.3 删除: 手柄防滑纵向凹槽 (用户要求平滑握持, 凹井按键自带触觉锚点)

// === 渲染精度 ===
$fa = 1;
$fs = 0.4;

// === 输出选择 ===
PART = "ALL";                // ALL / A / B / C / D / PREVIEW
RENDER_TOP_LEVEL = true;

// ====== 工具函数 ============================================================
function lerp(a, b, t) = a + (b - a) * t;
function smooth_lerp(t, p) = pow(max(0, min(1, t)), p);

// ====== 主杆轮廓函数（包络曲线，未含螺旋装饰） ==============================
//   返回任意 z 处主杆"包络外径"（含手柄、铜环、鳞纹带、雕花结、收颈、螺旋杖身、锥尖）
//   螺旋藤蔓装饰由独立模块在表面凸起加上，不在该函数内
function rod_dia(z) =
    // 1. Pommel 铜帽（多曲段倒角）
      z <  3                          ? lerp(pommel_dia_bot, pommel_dia_top, smooth_lerp(z/3, 1.0))
    : z <  pommel_z_top               ? pommel_dia_top
    // 2. 铜帽 → 手柄 平滑过渡（凹面收腰）
    : z <  handle_z_bot               ? lerp(pommel_dia_top, handle_dia_bot, smooth_lerp((z-pommel_z_top)/(handle_z_bot-pommel_z_top), 0.7))
    // 3. 手柄圆柱（轻微锥度）
    : z <  handle_z_top               ? lerp(handle_dia_bot, handle_dia_top, (z-handle_z_bot)/(handle_z_top-handle_z_bot))
    // 4. 上铜环（凸起短环 + 收口）
    : z <  handle_z_top + 1.5         ? lerp(handle_dia_top, ferrule_dia,    (z-handle_z_top)/1.5)
    : z <  ferrule_z_top - 1.5        ? ferrule_dia
    : z <  ferrule_z_top              ? lerp(ferrule_dia, band_dia, (z-(ferrule_z_top-1.5))/1.5)
    // 5. 鳞纹带（圆柱）
    : z <  band_z_top                 ? band_dia
    // 6. 雕花结（鼓起的椭球轮廓）
    : z <  band_z_top + 6             ? lerp(band_dia, knot_dia_max, smooth_lerp((z-band_z_top)/6, 0.8))
    : z <  knot_z_top - 6             ? knot_dia_max
    : z <  knot_z_top                 ? lerp(knot_dia_max, collar_dia, smooth_lerp((z-(knot_z_top-6))/6, 1.4))
    // 7. 收颈 + 上铜箍（v5.1.4: 把原 4mm Φ16 直筒改为 Φ19 鼓起金属环,
    //    与 ferrule 对称, 视觉上把雕花结/螺旋杖身"焊"在一起, 不再像断点）
    : z <  collar_z_top               ? collar_dia
    : z <  collar_z_top + 1           ? lerp(collar_dia, top_ferrule_dia, smooth_lerp((z-collar_z_top)/1, 0.7))
    : z <  collar_z_top + 3           ? top_ferrule_dia
    : z <  collar_z_top + 4           ? lerp(top_ferrule_dia, spiral_root_dia, smooth_lerp((z-collar_z_top-3)/1, 0.7))
    // 8. 螺旋杖身（包络锥度，藤蔓装饰由 spiral_vines_module 添加）
    : z <  spiral_z_top               ? lerp(spiral_root_dia, spiral_tip_dia, smooth_lerp((z-collar_z_top-4)/(spiral_z_top-collar_z_top-4), 1.0))
    // 9. 锥尖
    :                                   lerp(spiral_tip_dia, tip_dia, smooth_lerp((z-spiral_z_top)/(total_length-spiral_z_top), 1.3));

// ====== 主杆实体（rotate_extrude 一体成型 + 螺旋藤蔓） ======================
module solid_rod_envelope(z0, z1, segs = 280) {
    h    = z1 - z0;
    step = h / segs;
    points = [
        for (i = [0:segs]) [ rod_dia(z0 + i * step) / 2, i * step ]
    ];
    translate([0, 0, z0])
        rotate_extrude($fn = 96)
            polygon(points = concat(
                [[0, 0]],
                points,
                [[0, h]]
            ));
}

// ====== 螺旋藤蔓 v4.1（单股自然缠绕） =======================================
//   关键：藤蔓 2D 截面用"切向拉长的椭圆"代替正圆 ——
//     视觉上像一根缠绕在杖身的"扁枝"，而不是一颗球做螺旋拉伸
//   单股螺旋更接近天然木藤的不规则感（参考魔杖上手图右半段）
module vine_2d_profile(r_core, r_vine_radial, vine_aspect, n_vines) {
    union() {
        circle(r = r_core, $fn = 56);
        for (i = [0 : n_vines - 1])
            rotate([0, 0, 360 / n_vines * i])
                translate([r_core - r_vine_radial * 0.25, 0, 0])
                    // 切向（Y 轴）拉长，径向（X 轴）保持原宽，
                    // 让藤蔓断面像"鸡腰子形扁枝"
                    scale([1, vine_aspect, 1])
                        circle(r = r_vine_radial, $fn = 28);
    }
}

module spiral_shaft_decor() {
    h        = spiral_z_top - (collar_z_top + 4);
    twist    = spiral_turns * 360;
    r_root   = spiral_root_dia / 2;
    r_tip    = spiral_tip_dia  / 2;
    r_vine   = vine_height;                 // 藤蔓径向半径
    scale_t  = r_tip / r_root;

    translate([0, 0, collar_z_top + 4])
        linear_extrude(
            height = h,
            twist  = twist,
            slices = 240,                   // slices 提高让单股线条更光滑
            scale  = scale_t,
            convexity = 10
        )
            vine_2d_profile(
                r_core         = r_root - 0.05,
                r_vine_radial  = r_vine,
                vine_aspect    = vine_width_k,
                n_vines        = spiral_vines
            );
}

// ====== Pommel 铜帽（独立可拆段 D） =========================================
//   外形 = rotate_extrude 多段曲线，模拟车削的铜帽
//   底端有阴螺纹/榫孔可与手柄扣合
module pommel_module() {
    rotate_extrude($fn = 96) {
        polygon(points = [
            [0,                     0   ],
            [pommel_dia_bot/2 - 1,  0   ],
            [pommel_dia_bot/2,      0.6 ],
            [pommel_dia_bot/2 + 0.4, 1.5],
            [pommel_dia_top/2,      3.5 ],
            [pommel_dia_top/2,      pommel_z_top - 0.5],
            [pommel_dia_top/2 - 0.5, pommel_z_top],
            [0,                     pommel_z_top]
        ]);
    }
}

// ====== 鳞纹带表面装饰（环向 V 形深槽 + 端口锐线） ==========================
//   多道环槽组成"鳞纹"效果（全部减法），凹槽加深加宽以强化视觉
module band_decor_cut() {
    n_grooves = 5;
    for (i = [0 : n_grooves - 1]) {
        z = lerp(band_z_top - 16, band_z_top - 2, i / (n_grooves - 1));
        rotate_extrude($fn = 96)
            translate([band_dia/2 - 0.7, z, 0])
                polygon([[0, -1.0], [1.4, 0], [0, 1.0]]);   // 加深到 1.4 mm，加宽到 2.0 mm
    }
    // 顶/底端密集双线（车削锐角线）
    for (s = [0, 1, 2, 3])
        rotate_extrude($fn = 96)
            translate([band_dia/2 - 0.3, band_z_top - 0.4 - s * 0.7, 0])
                square([0.45, 0.4]);
}

// ====== 雕花结浮雕 v4.2（光滑水钻簇·24 颗圆顶 cabochon）====================
//   v4.1 用 4 棱台金字塔造"碎冰锐角"的方案确实漂亮，
//   但锐尖可能划伤用户的手 / 收纳袋 / 衣物，已改为
//   光滑圆顶 cabochon（半球凸起）——
//     赤道 12 颗大圆顶（主簇面）
//     上环  6 颗中圆顶（35°仰角）
//     下环  6 颗中圆顶（35°俯角）
//   每颗为半埋的圆球（高 $fn 保证表面光滑），凸起 ~1.0 mm。
//   保留密集的"水钻簇"视觉，无尖角无划伤风险。
module knot_relief_add() {
    z_mid  = (band_z_top + knot_z_top) / 2 + 1;
    r_knot = knot_dia_max / 2;

    // 单颗光滑圆顶 cabochon —— 半埋的圆球
    //   bump_r = 圆球半径
    //   embed  = 嵌入深度（0.5..0.7 ~ 半球露出，0.3 ~ 浅圆顶）
    module cabochon(bump_r) {
        sphere(r = bump_r, $fn = 32);
    }

    // 在球面 (φ azimuth, θ altitude) 处放一颗光滑圆顶
    //   anchor_r = 圆球中心到 wand 轴的距离（控制凸出量）
    module placed_cabochon(phi, theta, anchor_r, bump_r) {
        rotate([0, 0, phi])
            rotate([0, -theta, 0])
                translate([anchor_r, 0, 0])
                    cabochon(bump_r);
    }

    translate([0, 0, z_mid]) {
        // 赤道环：12 颗大圆顶（凸出 ~1.1 mm）
        for (i = [0 : 11])
            placed_cabochon(
                phi      = 30 * i,
                theta    = 0,
                anchor_r = r_knot - 0.5,        // 圆心略埋入 0.5 mm
                bump_r   = 1.6                   // 圆顶半径，凸出 1.1 mm
            );
        // 上环：6 颗中圆顶（凸出 ~0.9 mm，仰 35°）
        for (i = [0 : 5])
            placed_cabochon(
                phi      = 60 * i + 15,
                theta    = 35,
                anchor_r = r_knot - 1.4,
                bump_r   = 1.4
            );
        // 下环：6 颗中圆顶（凸出 ~0.9 mm，俯 35°）
        for (i = [0 : 5])
            placed_cabochon(
                phi      = 60 * i + 15,
                theta    = -35,
                anchor_r = r_knot - 1.4,
                bump_r   = 1.4
            );
    }
}

module knot_relief_cut() {
    // 雕花结上下两道短"领圈"凹环
    //   v5.1 修复 manifold: 上环 z 必须 *完全在 cabochon 上环球之外*
    //     cabochon 上环球顶 z = z_mid + anchor_r*sin(35°) + bump_r
    //                       = 149 + 7.23 + 1.4 = 157.63
    //     原 cut z=157.5..158.1 与球顶 0.13 mm 重叠 → CGAL non-manifold
    //   修复: 顶环 z=158.0..158.4 (距球顶 0.37 mm 余量)
    //         底环 z=137.5..137.9 (距 cabochon 下层球底 140.4 仍有 2.5 mm)
    cut_h = 0.4;        // 缩薄 0.6 → 0.4 减少与球的接近风险
    for (zr = [band_z_top + 0.5, knot_z_top - 1.0])
        rotate_extrude($fn = 96)
            translate([knot_dia_max/2 - 0.5, zr, 0])
                square([0.6, cut_h]);
}

// ====== 完整魔杖外形（实心，未打孔） ========================================
module wand_solid() {
    difference() {
        union() {
            // 1. Pommel 铜帽（pommel 段）
            pommel_module();
            // 2. 主杆包络（手柄 + 铜环 + 鳞纹带 + 雕花结 + 收颈 + 锥尖）
            //    螺旋杖身段 z = collar_z_top+4 .. spiral_z_top 在这里给出锥度包络
            //    实际上由 spiral_shaft_decor 替换/叠加（见后）
            //    此处包络用于"如果不要螺旋"或"段拆分"
            solid_rod_envelope(0, total_length);
            // 3. 螺旋藤蔓凸起
            spiral_shaft_decor();
            // 4. 雕花结赤道凸起
            knot_relief_add();
        }
        // 鳞纹带凹刻
        band_decor_cut();
        // 雕花结上下领圈
        knot_relief_cut();
    }
}

// ====== 内部空腔（电子腔 + PCB 卡槽 + 接口孔位 + 走线通道）==================
//
// PCB 在 wand 坐标系中的位置 (v5: PCB 板底 = 朝 pommel):
//   板中心 X=0, Y=0
//   PCB local (px, py) -> wand 坐标:
//     wand_X = px - pcb_w/2    (PCB 短边 28 mm 沿 X)
//     wand_Y = 0               (PCB 在 X-Z 平面, 厚度 ±Y)
//     wand_Z = cavity_z_pcb + py    (PCB local +Y = wand +Z)
//   即: PCB local y=0 (板顶, 含天线) -> wand_Z = cavity_z_pcb (...等等?)
//   重新明确: USB 在 PCB local y=38.09 (PCB 板的"下端"), 翻向后这一端朝 pommel.
//   所以 PCB local y 越大 -> wand_Z 越小. 公式:
//     wand_Z = cavity_z_pcb + (pcb_h - py)   (与之前一致)
//
// 元件开孔朝向约定:
//   +Y 壁  : LED1 / LED2 / SW1 (按键) / SW2 (开关) — 用户握持时朝向手心一侧
//   -Z 端  : USB-C (穿过 pommel 中心方孔)
function pcb_to_wand_z(py) = cavity_z_pcb + (pcb_h - py);
function pcb_to_wand_x(px) = px - pcb_w/2;

module wand_cavity() {
    // === 提前算出 PCB 卡槽 z 范围 ===
    //   卡槽起点必须在 handle 圆柱段内 (z >= handle_z_bot=14), 否则会穿出外壳
    //   下半段 PCB (z=5.9..15) 由 PCB seat 底托 + USB 接口陷入 pommel 方孔限位
    pcb_slot_z0 = max(cavity_z_pcb - 0.2, handle_z_bot + 1);   // 15
    pcb_slot_z1 = cavity_z_ant_top;                            // 56.63
    pcb_slot_h  = pcb_slot_z1 - pcb_slot_z0;

    union() {
        // ----------------------------------------------------------------
        // 1. 主电子腔 (圆柱) — 藏在手柄内
        //    Φ31 容纳 PCB 28×45 (角到圆心 14.02 < 15.5 ✓)
        // ----------------------------------------------------------------
        translate([0, 0, cavity_z_start])
            cylinder(h = cavity_len, d = cavity_id, $fn = 64);

        // ----------------------------------------------------------------
        // 2. PCB 卡槽 (沿 ±X 方向, 让 PCB 厚度方向被卡死, 防止旋转)
        //    cube 中心 X = ±pcb_w/2 (=±14, PCB 板边),  X 宽 = 2 (横跨板边 ±1mm)
        //    cube Y 宽 = 1.8 mm 夹紧 PCB 1.6mm 厚 (单边 0.1mm 间隙)
        //    v5.1.1 工艺: 卡槽顶端 1mm 加 45° 引导倒角让 PCB 自动找正滑入
        // ----------------------------------------------------------------
        for (sx = [-1, 1]) {
            // 主体卡槽 (z = pcb_slot_z0 .. pcb_slot_z1 - chamfer)
            translate([sx * pcb_w/2, 0,
                       pcb_slot_z0 + (pcb_slot_h - pcb_slot_chamfer_h)/2])
                cube([pcb_slot_depth, pcb_slot_w,
                      pcb_slot_h - pcb_slot_chamfer_h], center = true);
            // 入口倒角 (z = pcb_slot_z1 - chamfer .. pcb_slot_z1)
            //   底面 = 主卡槽尺寸, 顶面 = +1mm 四周扩张, hull 插值 = 45° 斜面
            hull() {
                translate([sx * pcb_w/2, 0, pcb_slot_z1 - pcb_slot_chamfer_h])
                    cube([pcb_slot_depth, pcb_slot_w, 0.01], center = true);
                translate([sx * pcb_w/2, 0, pcb_slot_z1])
                    cube([pcb_slot_depth + 2 * pcb_slot_chamfer_w,
                          pcb_slot_w + 2 * pcb_slot_chamfer_w,
                          0.01], center = true);
            }
        }

        // ----------------------------------------------------------------
        // 3. USB-C 方孔 — 从 pommel 中心向上穿到 PCB 板底
        //    USB 接口体长 7.4 mm 突出板外向 -Z, 孔从 z=-2 一路通到 PCB 底端
        //    z=-2 比 pommel 底面 z=0 还低 2 mm, 确保完全穿透外壳
        // ----------------------------------------------------------------
        let (usb_hole_w  = 9.0,
             usb_hole_t  = 4.0,
             usb_hole_z0 = -2,
             usb_hole_z1 = cavity_z_pcb + 0.5)
            translate([pcb_to_wand_x(usb_cx) - usb_hole_w/2,
                       -usb_hole_t/2,
                       usb_hole_z0])
                cube([usb_hole_w, usb_hole_t, usb_hole_z1 - usb_hole_z0]);

        // ----------------------------------------------------------------
        // 4. SW1 6mm 轻触按键 — +Y 外壁透通圆孔 (Φ5)
        //    只沿 +Y 方向贯穿 (从 PCB 表面 y=0.8 到凸台顶 y=18.5)
        //    用于嵌入独立打印的 part_button_pin (按键导柱)
        // ----------------------------------------------------------------
        translate([pcb_to_wand_x(sw1_cx), 10, pcb_to_wand_z(sw1_cy)])
            rotate([-90, 0, 0])             // cylinder 轴: +Z → wand +Y
                cylinder(h = 25, d = btn_pin_dia + btn_pin_clearance,
                         $fn = 32, center = true);

        // ----------------------------------------------------------------
        // 5. SW2 滑动开关 — +Y 外壁拨杆操作槽 (4 × 10 mm × 沿 +Y 贯穿)
        //    cube 中心 Y = 10, Y 范围 0..20 (从 PCB 表面到凸台顶)
        //    长方形开口沿 wand Z 方向 10 mm (匹配开关拨动行程)
        // ----------------------------------------------------------------
        translate([pcb_to_wand_x(sw2_cx), 10, pcb_to_wand_z(sw2_cy)])
            cube([sw2_slot_x, 22, sw2_slot_z], center = true);

        // ----------------------------------------------------------------
        // 6. LED1 / LED2 中心透光通道 (Φ2, 从 PCB 中心贯穿到外表面)
        //    v5.1.3: 外坑 Φ4 × 0.8 mm 改由 led_wells() 在 wand_full 中单独减
        //    这里只保留中心 Φ2 透光通道, 一路从 y=0 到 y=17.5 (略超外表面)
        //    后处理: 灌透明 UV 胶 / 嵌 Φ2 PMMA 棒 (从外侧凹井伸入)
        // ----------------------------------------------------------------
        for (led = [[led1_cx, led1_cy, 2.2],
                    [led2_cx, led2_cy, 2.0]]) {
            translate([pcb_to_wand_x(led[0]), 0, pcb_to_wand_z(led[1])])
                rotate([-90, 0, 0])
                    cylinder(h = r_outer_handle() + 0.5,  // 17.5
                             d = led[2], $fn = 24);
        }

        // ----------------------------------------------------------------
        // 7. 电池仓 4 道纵向限位筋 (实际是 cavity 圆柱外侧 ±Y 两道凸出, 用 difference 反向)
        //    注意: 这里 cavity 是被 difference 切除的 "空气", 凸筋应该是 *从 cavity 抽走*
        //    所以筋是负空间. 我们在 cavity 圆柱基础上 *减去* 4 道方块,
        //    让 cavity 内壁多出 4 道凸出 (筋), 夹住电池.
        // ----------------------------------------------------------------
        // 这一步通过外部 difference 已经处理: 我们在 cavity 内挖 4 道方块
        // 让筋 *变成 cavity 的一部分* — 即 4 个长方体减出 cavity 圆柱内的空间
        //
        // 实现: 在 cavity 圆柱内 *额外去除* 4 道竖向凹槽 (= 让筋凸进 cavity)
        // 等价: 这里不做处理, 改在 wand_solid 里用 add 形式加 4 道筋
        //   ↑ 但这会让筋出现在 cavity 之外, 进入 PCB 区
        // 正确做法: 不在 cavity 里减, 而是让 cavity 主圆柱本身就 "凹" 出 4 道凸进
        //
        // 简化方案: 加一个独立的 batt_ribs() 模块, 在 wand_full 里 union 进去
        // 此处 cavity 模块不处理, 保持纯空腔.

        // ----------------------------------------------------------------
        // 8. v5.1.7 PCB 工装销孔 (锁定 PCB 第 6 自由度)
        //    沿 -Y 方向贯穿外壳, 末端到达 PCB +Y 上方约 5mm
        //    用户装好 PCB 后, 从外壁 -Y 侧插入 Φ1.2 PLA 销 → 锁住 PCB
        // ----------------------------------------------------------------
        // 主通孔 (Φ1.3 沿 -Y 方向)
        //   起点 y = -20 (在外壁外, 确保完全穿透)
        //   终点 y = +5 (在 PCB +Y 上方, 给销末端留 5mm "暂存空间")
        translate([pcb_pin_x, -20, pcb_pin_z])
            rotate([-90, 0, 0])         // 圆柱轴 +Z 转到 wand +Y
                cylinder(h = 25, d = pcb_pin_hole_dia, $fn = 24);
        // 销头浅井 (Φ3.2 × 0.6 mm 在外壁 -Y 侧, 容纳销头 Φ3 凸缘齐平)
        //   井从外壁 -Y 表面 (y ≈ -17, handle 外径 Φ34) 向 -Y 侧凿入 0.6mm
        translate([pcb_pin_x, -(handle_dia_bot/2 + 0.5), pcb_pin_z])
            rotate([-90, 0, 0])
                cylinder(h = pcb_pin_well_d + 0.6, d = pcb_pin_well_dia, $fn = 32);
    }
}

// ====== 电池仓限位筋 (4 道纵向凸筋, 夹住电池防晃) ============================
// 设计说明:
//   电池 30(W) × 6(t) × 40(L) mm, 沿 wand 轴 Z 立放
//   X 方向半宽 15 vs cavity 半径 15.5, X 间隙仅 0.5 mm — 不需要支撑
//   Y 方向半厚 3  vs cavity 半径 15.5, Y 间隙 12.5 mm — 必须加筋夹住
//
//   筋形态: 从 cavity 内壁 (r=15.5) 一路延伸到电池表面 (y=±3.5, 留 0.5 间隙)
//          长方体, 截面 1.5(沿切向 X) × 12(沿径向 Y), 高 = 电池长 40
//   位置: ±Y 两侧, X 偏移 ±10 mm (避开正中)
//   连接: 必须连到外壳实体, 否则会成孤立体. 因此 rib 从 y=cavity_id/2 起延伸
//          (从 cavity 圆柱被切除的"边界"开始, 即 rib 占据 cavity 边缘 + 内部)
module batt_ribs() {
    rib_z0  = cavity_z_batt;
    rib_z1  = cavity_z_batt + batt_l;
    rib_h_z = rib_z1 - rib_z0;
    // 筋径向起点: 紧贴 cavity 圆边 (cavity 半径 15.5)
    rib_y_outer = cavity_id/2;          // 15.5
    // 筋径向终点: 略大于电池半厚 (留 0.5 间隙便于电池滑入)
    rib_y_inner = batt_t/2 + 0.5;       // 3.5
    rib_y_len   = rib_y_outer - rib_y_inner;
    // 用 intersection 把每道筋限制在 cavity 圆柱内, 不会穿出外壳
    intersection() {
        union() {
            for (sy = [-1, 1])           // ±Y 两侧
            for (sx = [-1, 1])           // ±X 偏置 (左右各两条, 总共 4 道)
                translate([sx * 10 - batt_rib_w/2,
                           sy * rib_y_outer - (sy > 0 ? rib_y_len : 0),
                           rib_z0])
                    cube([batt_rib_w, rib_y_len, rib_h_z]);
        }
        // 限制在 cavity 圆柱内 (留 0.1 mm 余量保证 union 时筋边贴到 cavity 内壁)
        translate([0, 0, rib_z0 - 0.1])
            cylinder(h = rib_h_z + 0.2, d = cavity_id + 0.2, $fn = 64);
    }
}

// ====== PCB 底端定位台 (沿 Z 阻止 PCB 下滑撞 USB-C 接口体) ===================
// 设计说明:
//   位于 z = cavity_z_pcb - pcb_seat_t 处的薄平台 (厚 1.0 mm)
//   宽度 = PCB_w 减去 USB 接口宽度 (避开 USB 接口体不要顶住)
//   实际做成 *两段* 在 PCB 底两侧, 中间留出 USB 接口避位
module pcb_seat() {
    seat_z = cavity_z_pcb - pcb_seat_t;
    // USB 接口区 X 范围
    usb_x_lo = pcb_to_wand_x(usb_cx) - 4.5;       // -9.32
    usb_x_hi = pcb_to_wand_x(usb_cx) + 4.5;       // -0.32
    // 左侧定位台: x ∈ [-pcb_w/2, usb_x_lo]
    seat_left_w = usb_x_lo - (-pcb_w/2);          // 4.68
    if (seat_left_w > 1.0)
        translate([-pcb_w/2, -pcb_t/2 - 0.5, seat_z])
            cube([seat_left_w, pcb_t + 1.0, pcb_seat_t]);
    // 右侧定位台: x ∈ [usb_x_hi, pcb_w/2]
    seat_right_w = pcb_w/2 - usb_x_hi;            // 14.32
    if (seat_right_w > 1.0)
        translate([usb_x_hi, -pcb_t/2 - 0.5, seat_z])
            cube([seat_right_w, pcb_t + 1.0, pcb_seat_t]);
}

// ====== v5.1.3 移除防滑纹 ====================================================
// v5.1.2 的 grip_grooves_cut() 已删除 - 用户要求手柄完全平滑握持
// 防滑功能由凹陷式按键井 (sw1_press_well) 自动提供 - 拇指落在井里就有触觉锚点
// 天线避让逻辑也不再需要: 没有防滑纹诱导食指, 用户握姿自由

// ====== v5.1.3 内部加厚岛 (cavity 内壁向 +Y 反凸, 外表面保持平滑) ============
// 设计说明:
//   v5.1.2 把"按钮区加厚"做成 *外凸* 椭圆岛 (wall_boss), 用户握持时硌手.
//   v5.1.3 改成 *内凸*: 从 cavity 内壁 (y=15.5) 向 +Y 方向反凸 1.5 mm,
//          局部内壁退到 y=14, 外壳总壁厚从 1.5 增到 3.0 mm.
//   外表面保持完美 Φ34 → Φ32 的圆锥面, 用户握持手感平滑无突起.
//
// 内凸岛形态: 矩形截面 (沿 X / Z 方向), 圆角过渡 (用 hull 包络)
// 覆盖范围: 一整块连续岛覆盖 SW1 + SW2 + LED1 + LED2 全部 4 个功能件
//          (z 范围 5..60, x 范围 -16..+16 切向)
//          连续加厚比分散 4 个小岛更省 PCB 空间, 也避免 cavity 内壁不规则
//
// 注意: PCB 板表面在 y=0.8, 加厚后内壁 y=14, 间隔 13.2 mm 充足
//       SW1/SW2/LED 元件最高凸出 PCB 表面 5 mm (y_top=5.8), 距内壁 8.2 mm
//       加厚岛只覆盖 z=5..60, 完全错开电池区 (z=56..96), 不挤压电池
function r_outer_handle() = handle_dia_bot / 2;        // 17 (外表面)
function r_inner_thicken() = cavity_id/2 - thicken_inward_t;  // 14 (加厚后内壁)

module wall_thicken_inward() {
    // 一整块矩形板, 覆盖 SW1+SW2+LED1+LED2 全部位置 + 边缘融合
    //   x 范围: ±16 mm (略大于 PCB 半宽 14, 切向覆盖所有元件)
    //   y 范围: y_inner_thicken (=14) .. y_outer_handle (=17, 伸到外壁内表面再多 0.1)
    //   z 范围: thicken_inward_z0 (=5) .. thicken_inward_z1 (=60)
    // 用 intersection 限制在 cavity 圆柱内, 避免凸出主杆外
    intersection() {
        translate([-16, r_inner_thicken(), thicken_inward_z0])
            cube([32,
                  r_outer_handle() - r_inner_thicken() + 0.1,
                  thicken_inward_z1 - thicken_inward_z0]);
        // 限制在 wand_solid 外壳内 (按 handle 段最大半径 17 取保守圆柱)
        cylinder(h = thicken_inward_z1 + 1, r = r_outer_handle(),
                 $fn = 64);
    }
}

// ====== v5.1.3 完整魔杖 (平滑外壁 + 内部加厚 + 凹陷式按键/LED) ==============
//   构造顺序:
//     1) wand_solid + wall_thicken_inward 合并 (外壳实体 + 内部加厚岛)
//     2) 减去 wand_cavity (空腔 + SW1/SW2/LED 透通孔, 贯穿加厚岛)
//     3) 减去 sw1_press_well (按键凹井 Φ12 × 1mm, 用户拇指自然按下)
//     4) 减去 sw2_slide_recess (拨杆滑槽 4×12mm × 0.6mm, 平滑过渡)
//     5) 减去 led_wells (2 个 Φ4 × 0.8mm LED 凹坑, 扩散光晕)
//     6) 加回 batt_ribs / pcb_seat (内部电池/PCB 定位)
//
// 用户体验差异 (v5.1.2 vs v5.1.3):
//     v5.1.2: 外表面有 4 个椭圆凸台 + 8 道防滑纹, 像 "工业产品"
//     v5.1.3: 外表面 100% 光滑, 按键/LED 都凹陷, 像 "魔杖" + "现代手柄"
module wand_full() {
    union() {
        difference() {
            union() {
                wand_solid();              // 外壳实体 (圆锥外形)
                wall_thicken_inward();     // 内部加厚岛 (cavity 内壁反凸 1.5mm)
            }
            wand_cavity();                 // 空腔 + 全部透通孔 (贯穿加厚岛)
            sw1_press_well();              // SW1 凹井 Φ12 × 深 1.0 mm
            sw2_slide_recess();            // SW2 拨杆滑槽 4×12 × 深 0.6 mm
            led_wells();                   // LED1/LED2 Φ4 × 深 0.8 mm 凹坑
        }
        batt_ribs();                       // 电池仓 4 道纵向筋
        pcb_seat();                        // PCB 底端定位台
    }
}

// ====== v5.1.3 SW1 按键凹井 (从平滑外表面凹下 1mm 圆形井, 用户拇指按下) ====
// 设计说明:
//   外表面 r=17 处沿 -Y 方向凹下 1.0 mm, 形成 Φ12 圆形井 (井底 y=16)
//   井底再开 Φ5 透通孔 (与 wand_cavity 第 4 项对应, 容纳按键导柱主柱)
//   用户拇指自然伸入井按下导柱凸缘 → 凸缘下沉 0.4 mm → 触发 SW1
//
// 几何参数:
//   井直径    = sw1_well_d = 12 mm  (够大让拇指自然按下, 比凸缘 Φ10 大 2mm)
//   井深      = sw1_well_dep = 1.0 mm (导柱凸缘 Φ10×0.6mm 沉入后留 0.4mm 行程)
//   井底壁厚  = (17-1.0) - 14 = 2.0 mm 安全 (内部已加厚到 r_inner=14)
//
// 工艺细节:
//   井口边缘做 0.3 mm × 45° 倒角防止印刷毛边伤手 (用 rotate_extrude 旋转环)
sw1_well_d        = 12.0;     // 凹井直径
sw1_well_dep      = 1.0;      // 凹井深度
sw1_well_chamfer  = 0.3;      // 井口倒角半径 (打印 friendly)

module sw1_press_well() {
    cx = pcb_to_wand_x(sw1_cx);
    cz = pcb_to_wand_z(sw1_cy);
    r_outer = r_outer_handle();   // 17

    // 主井 (圆柱凹陷, 从 r=17 向 -Y 凹 sw1_well_dep)
    translate([cx, r_outer - sw1_well_dep + 0.05, cz])
        rotate([-90, 0, 0])
            cylinder(h = sw1_well_dep + 0.1, d = sw1_well_d, $fn = 64);

    // 井口外缘 45° 倒角 (= 一圈外大内小的环锥)
    //   外径 = sw1_well_d + 2*chamfer (Φ12.6), 内径 = sw1_well_d (Φ12)
    //   高度 = chamfer (0.3mm), 从外表面 y=17 向 -Y
    translate([cx, r_outer - sw1_well_chamfer + 0.05, cz])
        rotate([-90, 0, 0])
            difference() {
                cylinder(h = sw1_well_chamfer + 0.1,
                         d1 = sw1_well_d + 2 * sw1_well_chamfer,
                         d2 = sw1_well_d,
                         $fn = 64);
                translate([0, 0, -0.1])
                    cylinder(h = sw1_well_chamfer + 0.3,
                             d = sw1_well_d - 0.1, $fn = 64);
            }
}

// ====== v5.1.3 SW2 拨杆滑槽 (扁平浅槽 + 内部贯穿孔) =========================
// 设计说明:
//   外表面凹下 0.6 mm 的圆角矩形浅槽 (4×12mm), 拇指/食指可方便操作拨杆
//   槽底再开 4×10 mm 透通孔 (与 wand_cavity 第 5 项对应, 露出 SW2 拨杆)
//
// 几何参数:
//   外槽:  4 (X) × 12 (Z) × 0.6 mm (Y)
//   内孔:  4 × 10 mm (与 wand_cavity 中 sw2_slot_x/sw2_slot_z 一致)
//   槽底壁厚 = (17-0.6) - 14 = 2.4 mm 安全
sw2_recess_w   = 4.0;
sw2_recess_h   = 12.0;
sw2_recess_dep = 0.6;
sw2_recess_r   = 1.0;       // 圆角矩形 4 个角的半径

module sw2_slide_recess() {
    cx = pcb_to_wand_x(sw2_cx);
    cz = pcb_to_wand_z(sw2_cy);
    r_outer = r_outer_handle();

    // 圆角矩形凹槽: 用 hull 把 4 个圆柱包成圆角方块
    translate([cx, r_outer - sw2_recess_dep + 0.05, cz])
        rotate([-90, 0, 0])
            linear_extrude(height = sw2_recess_dep + 0.1) {
                hull() {
                    for (sx = [-1, 1])
                    for (sy = [-1, 1])
                        translate([sx * (sw2_recess_w/2 - sw2_recess_r),
                                   sy * (sw2_recess_h/2 - sw2_recess_r)])
                            circle(r = sw2_recess_r, $fn = 32);
                }
            }
}

// ====== v5.1.3 LED 凹光井 (Φ4 圆坑, 直接在外表面凹下 0.8 mm) =================
// 设计说明:
//   原 v5.1.2 凸台 Φ8 + Φ2.5 中心坑 → 用户握持时虎口压住中心坑看不到 LED
//   v5.1.3 改成: 外表面凹 Φ4 × 深 0.8 mm 圆坑, 中心 Φ2 通道继续贯穿到 PCB
//   Φ4 比 Φ2.5 大 60%, 形成"光晕扩散区", 灌透明 UV 胶后从 4mm 范围扩散光
//   即使虎口部分覆盖, 边缘 4mm 也能透光
//
// 几何参数:
//   坑径    = led_well_d = 4.0 mm
//   坑深    = led_well_dep = 0.8 mm
//   坑底壁厚 = (17-0.8) - 14 = 2.2 mm 安全
led_well_d   = 4.0;
led_well_dep = 0.8;

module led_well(cx, cz) {
    r_outer = r_outer_handle();
    translate([cx, r_outer - led_well_dep + 0.05, cz])
        rotate([-90, 0, 0])
            cylinder(h = led_well_dep + 0.1, d = led_well_d, $fn = 32);
}

module led_wells() {
    led_well(pcb_to_wand_x(led1_cx), pcb_to_wand_z(led1_cy));
    led_well(pcb_to_wand_x(led2_cx), pcb_to_wand_z(led2_cy));
}

// ====== PCB / 电池占位（PREVIEW 用，反映真实尺寸 + 元件位置）===============
// 用于 render_preview.scad 切剖图, 直观验证 PCB 嵌入是否对齐.
module preview_payload() {
    // ---- PCB 主体 28×45×1.6 mm ----
    color("forestgreen", 0.85)
        translate([0, 0, cavity_z_pcb])
            translate([-pcb_w/2, -pcb_t/2, 0])
                cube([pcb_w, pcb_t, pcb_h]);

    // ---- ESP32 模组占位 18×25.5 mm, 含天线突出板顶 5.73 mm ----
    color("dimgray", 0.95)
        translate([pcb_to_wand_x(5.23), pcb_t/2, cavity_z_pcb_top - 25.5 + pcb_antenna_overhang])
            cube([18, 3, 25.5]);  // 模组贴 +Y 表面, 厚 3 mm

    // ---- USB-C 16pin 占位 (8.5×7.4×3.2 mm), 接口在 PCB 板底突出 -Z ----
    //   接口体顶端 = PCB 板底 (cavity_z_pcb)
    //   接口开口端 = cavity_z_pcb - 7.4 (突出 pommel 底 1.5 mm)
    color("silver", 0.95)
        translate([pcb_to_wand_x(usb_cx) - 8.5/2, -3.2/2, cavity_z_pcb - 7.4])
            cube([8.5, 3.2, 7.4]);

    // ---- SW1 6mm 轻触按键体 6×6×5 mm, 按键帽朝 +Y ----
    color("ivory", 0.95)
        translate([pcb_to_wand_x(sw1_cx) - 3, pcb_t/2, pcb_to_wand_z(sw1_cy) - 3])
            cube([6, 5, 6]);

    // ---- SW2 SMD 滑动开关 7×3×2 mm, 拨杆朝 +Y ----
    color("lightgray", 0.95)
        translate([pcb_to_wand_x(sw2_cx) - 3.5, pcb_t/2, pcb_to_wand_z(sw2_cy) - 1])
            cube([7, 2, 3]);

    // ---- LED1 (绿色) ----
    color("lawngreen", 1.0)
        translate([pcb_to_wand_x(led1_cx), pcb_t/2 + 0.5, pcb_to_wand_z(led1_cy)])
            rotate([-90, 0, 0])
                cylinder(h = 1, d = 1.6, $fn = 16);

    // ---- LED2 (红色: 充电指示) ----
    color("red", 1.0)
        translate([pcb_to_wand_x(led2_cx), pcb_t/2 + 0.5, pcb_to_wand_z(led2_cy)])
            rotate([-90, 0, 0])
                cylinder(h = 1, d = 1.6, $fn = 16);

    // ---- 电池 30×40×6 mm 竖立 (厚边沿 Y) ----
    color("orange", 0.9)
        translate([0, 0, cavity_z_batt + batt_l/2])
            cube([batt_w, batt_t, batt_l], center = true);
}

// ====== 段间装配 v5.1.5: M10×1.5 公制螺纹 ====================================
//
// metric_thread: 简化的 ISO 60° 三角齿公制螺纹, 由 linear_extrude(twist) 实现
//   d_maj    = 公称直径 (外螺纹外径; 内螺纹设为名义孔径)
//   p        = 节距 (mm)
//   h        = 螺纹有效啮合长度
//   internal = false: 外螺纹实体, 直接当公柱用
//              true : 用作内螺纹母孔 (调用方 difference 自己减出)
//                     internal=true 时齿径 +0.30 (单边), FDM 装配公差
//
// 实现细节:
//   1) 截面 = 中心圆 (r=r_min) + 一个径向三角齿凸 (r=r_min..r_maj)
//   2) linear_extrude(height=h, twist=-360*h/p) 让截面沿 +Z 螺旋上升
//      每升 p 完成一圈, 形成一道连续的螺纹齿
//   3) 齿深 = 0.6 p (近似 ISO Metric 5/8 H, 对 FDM 打印齿不太尖也不太深)
//
// 打印朝向建议: 螺纹中心轴 = Z 轴 = 打印床法线方向, 齿是逐层堆叠形成,
//               不会出现 >45° 悬空, 不需支撑. 对 FDM 极友好.
module metric_thread(d_maj, p, h, internal = false, inner_dia = 0, fn = 48) {
    cl       = internal ? 0.30 : 0;
    r_maj    = d_maj / 2 + cl;
    r_min    = r_maj - 0.60 * p;            // 齿深 0.6 p
    n_turn   = h / p;
    twist    = -360 * n_turn;
    tooth_y  = p / 3;                       // 齿在切向跨度 (≈ 1/3 节距)
    eps      = 0.05;                        // 截面联合时极小重叠, 防 manifold

    // inner_dia > 0 时减出中央通孔 (空心螺纹), 用于 D-A 接缝让 USB 穿过
    difference() {
        linear_extrude(height = h, twist = twist,
                       slices = max(60, round(fn * n_turn)),
                       convexity = 4) {
            union() {
                circle(r = r_min, $fn = fn);
                polygon([
                    [r_min - eps, -tooth_y],
                    [r_maj,        0      ],
                    [r_min - eps,  tooth_y],
                ]);
            }
        }
        if (inner_dia > 0)
            translate([0, 0, -0.5])
                cylinder(h = h + 1, d = inner_dia, $fn = fn);
    }
}

// joint_male: 公段顶部凸出 M10×1.5×5mm 外螺纹, 直接当实体凸柱使用
//   z = 公段主体顶面 z 坐标 (从该 z 起向 +Z 凸出 joint_len mm)
module joint_male(z, d = joint_dia, p = joint_pitch, h = joint_len) {
    translate([0, 0, z])
        metric_thread(d_maj = d, p = p, h = h, internal = false);
}

// joint_female: 母段底部内螺纹孔, 由调用方 difference 减出
//   z = 母段主体底面 z 坐标 (从该 z 起向 +Z 挖 joint_len+0.2 mm)
//   入口下沉 0.1mm 让公螺纹起始齿无障碍咬入
module joint_female(z, d = joint_dia, p = joint_pitch, h = joint_len) {
    translate([0, 0, z - 0.1])
        metric_thread(d_maj = d, p = p, h = h + 0.2, internal = true);
}

// ====== 段 D：Pommel 铜帽（v5.1.6: M16×2 空心螺纹连接, 免胶水） =============
// 装配工艺: 用户对齐 SW1 朝向 → 把 A handle 套到 D pommel 上 → 顺时针拧 2 整圈
//             螺纹自锁, 不需要任何胶水. 想拆开维护 PCB / 换电池, 反向拧出即可.
// 几何要点:
//   1) pommel 主体 (z=0..8) 不变, USB 方孔贯穿中心
//   2) 顶部凸出 M16×2 空心螺纹 (z=8..12, 外径 16, 内孔 10)
//      内孔 Φ10 让 USB-C 9×4 接口体顺利穿过 pommel 接到 PCB 板底
//   3) 螺纹凸柱外侧到 pommel 边缘 (Φ22) 之间留 (22-16)/2=3mm 平台,
//      作为 A handle 主体 Φ34 拧到底时的轴向止位面
module part_pommel() {
    difference() {
        union() {
            pommel_module();
            // M16×2×4 空心螺纹凸柱 (z=8..12) — D-A 接缝公螺纹
            translate([0, 0, pommel_z_top])
                metric_thread(d_maj = da_thread_d, p = da_thread_p,
                              h = da_thread_h, internal = false,
                              inner_dia = da_thread_id);
        }
        // USB 方孔贯穿 pommel + 螺纹凸柱 (z = -1 .. 13)
        translate([pcb_to_wand_x(usb_cx) - 9.0/2, -4.0/2, -1])
            cube([9.0, 4.0, pommel_z_top + da_thread_h + 2]);
    }
}

// ====== 段 A：Handle 手柄段（v5.1.6: M16×2 空心螺纹母孔 + M10 顶部公螺纹） ===
// 双接缝:
//   (1) 底部 z=8: M16 空心螺纹母孔, 与 D pommel 公螺纹咬合
//                 中央 Φ10 通孔留给 USB-C 接口体穿过到 PCB
//   (2) 顶部 z=112: M10×1.5 公螺纹凸柱, 拧入 B decor 母孔
module part_handle() {
    union() {
        difference() {
            intersection() {
                wand_full();
                translate([-50, -50, pommel_z_top])
                    cube([100, 100, handle_z_top - pommel_z_top]);
            }
            // (1) D-A 接缝母孔: M16×2 内螺纹 + 中央 Φ10 USB 通道
            //     母孔 z 范围 = 7.9 .. 12.1 (= h+0.2, 上下各 0.1mm 入口)
            translate([0, 0, pommel_z_top])
                metric_thread(d_maj = da_thread_d, p = da_thread_p,
                              h = da_thread_h + 0.2, internal = true,
                              inner_dia = da_thread_id);
            // 入口下沉 0.1mm: 让公螺纹起始齿无障碍咬入
            translate([0, 0, pommel_z_top - 0.1])
                cylinder(h = 0.15, d = da_thread_d + 0.6, $fn = 64);
        }
        // (2) A-B 接缝公柱: M10×1.5×5 螺纹凸出
        joint_male(handle_z_top);
    }
}

// ====== 段 B：Decor 雕花段（z = handle_z_top .. collar_z_top） ===============
//   v5.1 manifold 修复: cube 顶端 z 必须严格小于 spiral 起点 (collar_z_top+4),
//     否则 spiral 截面恰好在切割面会产生 CGAL non-manifold 边
//   spiral 起点 z=168, cube 顶 z=167.95 (差 0.05 mm), C 段会从 z=168 继续, 0.05 mm 缝
//   被段间装配榫 joint_male/female 完全覆盖, 不影响装配
module part_decor() {
    cube_top_z = collar_z_top + 4 - 0.05;   // 167.95
    union() {
        difference() {
            intersection() {
                wand_full();
                translate([-50, -50, handle_z_top])
                    cube([100, 100, cube_top_z - handle_z_top]);
            }
            joint_female(handle_z_top);
        }
        joint_male(collar_z_top + 4);
    }
}

// ====== 段 C：Spiral Shaft + Tip（z = collar_z_top+4 .. total_length） ======
module part_shaft() {
    difference() {
        intersection() {
            wand_full();
            translate([-50, -50, collar_z_top + 4])
                cube([100, 100, total_length - (collar_z_top + 4) + 1]);
        }
        joint_female(collar_z_top + 4);
    }
}

// ====== 段 E v5.1.3：凹陷式按键导柱 (大薄凸缘, 沉入手柄凹井) ===============
//
// 几何 (沿 +Z 立向打印, 大薄凸缘朝下):
//   [Φ10 大薄凸缘] --- 顶端 (z=0..0.6) 沉入手柄 Φ12 凹井, 用户拇指按下面
//   [Φ4.6 柱体]   --- 中段 (z=0.6..0.6+pin_h) 穿过外壳壁 + 触压 SW1
//   [Φ4 顶尖]     --- 底端 (z=0.6+pin_h..0.6+pin_h+1) 略小, 减摩擦顶 SW1 帽
//
// pin_h 计算 (v5.1.3 修订):
//   外壳外径 = handle_dia_bot = 34 mm, 半径 17
//   按键凹井底 y = 17 - sw1_well_dep = 16
//   按键内部加厚后内表面 y = 14 (cavity_id/2 - thicken_inward_t)
//   主柱穿过段 (从凹井底 y=16 进入, 到 SW1 帽顶 y=5.8) = 16 - 5.8 = 10.2 mm
//   预压 0.3 mm  → 主柱长 pin_main_h = 9.9 mm (凹缘下还有 0.4mm 行程, 总下沉 0.7)
//
//   总长 (含凸缘 + 顶尖) = 0.6 + 9.9 + 1.0 = 11.5 mm
//
// 装配:
//   凸缘 Φ10 < 凹井 Φ12, 单边间隙 1mm 让用户拇指可伸入按下凸缘表面
//   凸缘表面比手柄外圆低 (1.0 - 0.6 = 0.4 mm), 完全不外凸, 不勾手
module part_button_pin() {
    pin_main_h  = 9.9;
    pin_tip_h   = 1.0;
    cap_dia     = 10.0;     // v5.1.3 大薄凸缘 (沉入 Φ12 井)
    cap_t       = 0.6;      // v5.1.3 凸缘减薄 (留 0.4mm 行程)
    color("ivory")
        difference() {
            union() {
                // 顶端大薄凸缘 (Φ10 × 0.6mm), 朝 -Z 方向 (装配时朝外壳外侧)
                translate([0, 0, 0])
                    cylinder(h = cap_t, d = cap_dia, $fn = 64);
                // 主柱 (Φ4.6 × pin_main_h)
                translate([0, 0, cap_t])
                    cylinder(h = pin_main_h, d = btn_pin_dia, $fn = 32);
                // 顶尖 (Φ4 × 1mm), 减少与 SW1 帽接触面摩擦
                translate([0, 0, cap_t + pin_main_h])
                    cylinder(h = pin_tip_h, d = 4.0, $fn = 32);
            }
            // ---- 凸缘外端 (用户能摸到的面) Φ6 × 0.3 mm 居中浅指坑 ----
            //   让用户拇指自然找到"按钮中心点", 凹陷井 + 凸缘指坑双重定位
            //   v5.1.3: 凸缘加大后, 中心指坑也加大 (Φ3 → Φ6)
            translate([0, 0, -0.05])
                cylinder(h = 0.35, d = 6.0, $fn = 64);
        }
}

// ====== 段 F: PCB 工装销 (v5.1.7) ============================================
// 装配时用户从 A handle 外壁 -Y 侧的 Φ1.3 通孔插入此销, 穿过 PCB 板的 Φ1.18
// 工厂定位孔, 锁定 PCB 不能 +Z 反弹. 装好后销头 Φ3 凸缘嵌入外壳浅井齐平.
// 销头底面磨掉一小圈 (Φ2.5×0.2mm 凹) 留指甲槽, 用户可以用指甲撬出维护.
module part_pcb_pin() {
    color("ivory")
        difference() {
            union() {
                // 主销 Φ1.2 × pcb_pin_len
                cylinder(h = pcb_pin_len, d = pcb_pin_dia, $fn = 16);
                // 销头 Φ3 装饰圆点 (沉入外壳浅井)
                translate([0, 0, pcb_pin_len])
                    cylinder(h = pcb_pin_cap_t, d = pcb_pin_cap_dia, $fn = 32);
            }
            // 销头底面指甲槽 Φ2.5 × 0.2mm (从 -Y 表面凹入)
            translate([0, 0, pcb_pin_len + pcb_pin_cap_t - 0.2])
                cylinder(h = 0.25, d = 2.5, $fn = 32);
            // 销尖端 45° 倒角 (装配时容易找正 PCB 定位孔)
            translate([0, 0, -0.01])
                cylinder(h = 0.3, d1 = pcb_pin_dia + 0.2, d2 = 0.6, $fn = 16);
        }
}

// ====== 主入口 ==============================================================
module render_part(p = PART) {
    if      (p == "A")        color("saddlebrown")  part_handle();
    else if (p == "B")        color("saddlebrown")  part_decor();
    else if (p == "C")        color("saddlebrown")  part_shaft();
    else if (p == "D")        color("darkgoldenrod") part_pommel();
    else if (p == "E")        part_button_pin();
    else if (p == "F")        part_pcb_pin();
    else if (p == "PREVIEW")  {
        color("saddlebrown") wand_full();
        preview_payload();
        // 按键导柱预装位 (顶尖贴到 SW1 帽)
        translate([pcb_to_wand_x(sw1_cx), 14, pcb_to_wand_z(sw1_cy)])
            rotate([90, 0, 0])
                part_button_pin();
    }
    else {
        // ALL: 整体上色（铜帽 + 上铜环 vs 杖身木色）
        color("darkgoldenrod") pommel_module();
        // 主体木色（pommel 区域被 cube 切除，避免重复着色）
        difference() {
            color("saddlebrown") wand_full();
            translate([-50, -50, -0.1]) cube([100, 100, pommel_z_top + 0.1]);
        }
    }
}

if (RENDER_TOP_LEVEL) render_part();
