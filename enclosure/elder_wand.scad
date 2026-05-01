// ============================================================================
//  CyberWand v4.0 — 葡萄藤雕花魔杖（按 enclosure/魔杖上手图.png 重塑）
//
//  v4 设计理念变更（重大）：
//    × v3 多球簇 Elder Wand 风格 (复刻邓布利多老魔杖)
//    √ v4 单一手柄 + 雕花结 + 藤蔓螺旋杖身（参考"魔杖上手图"，
//        整体造型纤细，PCB 竖向沿柄轴摆放，杖身可大幅瘦身）
//
//  整体节奏：
//    [Pommel铜帽] [手柄圆柱] [上铜环] [鳞纹带] [雕花结球] [收颈] [螺旋杖身] [锥尖]
//
//  电子件布置（相对 v3 重大变更）：
//    PCB 35×25×1.6 + 电池 40×30×6 沿柄轴端到端"竖向叠放"
//      → cavity 圆柱 Φ31 × 80 mm（藏在手柄内）
//    USB-C / 按键 / LED / 开关接口仍开在手柄侧面
//
//  外形参考: enclosure/魔杖上手图.png
//  设计文档: enclosure/elder_wand_design.md（v4 章节）
// ============================================================================

// ====== CONFIG 区 ===========================================================
total_length     = 360;

// === 段位 z 边界 ===
pommel_z_top     =   8;     // Pommel 铜帽顶端
handle_z_bot     =  14;     // 手柄底端（与 Pommel 平滑过渡完成）
handle_z_top     = 104;     // 手柄顶端
ferrule_z_top    = 111;     // 上铜环顶
band_z_top       = 129;     // 鳞纹带顶
knot_z_top       = 151;     // 雕花结顶
collar_z_top     = 156;     // 收颈段顶（接进螺旋杖身）
spiral_z_top     = 330;     // 螺旋杖身顶（接锥尖）
//                360       // 锥尖

// === 直径参数 ===
pommel_dia_bot   = 18;      // Pommel 铜帽底
pommel_dia_top   = 22;      // Pommel 铜帽顶
handle_dia_bot   = 34;      // 手柄底（接 pommel）
handle_dia_top   = 32;      // 手柄顶（轻微锥度，更符合手感）
ferrule_dia      = 33;      // 上铜环外径（略凸于手柄顶）
band_dia         = 24;      // 鳞纹带外径
knot_dia_max     = 28;      // 雕花结最宽处
collar_dia       = 16;      // 收颈段（雕花结接到杖身）
spiral_root_dia  = 16;      // 螺旋杖身根
spiral_tip_dia   =  4;      // 螺旋杖身梢（接锥尖）
tip_dia          =  1.2;    // 最终锐尖

// === PCB / 电池实物 ===
pcb_w  = 25;   pcb_l  = 35;   pcb_t = 1.6;
batt_w = 30;   batt_l = 40;   batt_t = 6;

// === 电子腔（圆柱形，藏在手柄内） ===
//   配重原则：重电池靠近 pommel 底端（手腕侧），轻 PCB 上方（指尖侧）
//   v 形排布：[底盘螺孔] [batt 40mm] [4mm 间隔] [PCB 35mm] [腔顶] = 79mm
cavity_id        = 31;
cavity_len       = 82;
cavity_z_start   = 16;       // pommel 铜帽以上 2 mm 起
cavity_z_batt    = 18;       // 电池起始（贴近 pommel，重心下移）
cavity_z_pcb     = 62;       // PCB 起始（电池上方 4 mm）

// === 螺旋雕刻参数（v4.1 单股自然螺旋） ===
spiral_turns     = 2.2;      // 单股需要更多圈数才有"缠绕感"
spiral_vines     = 1;        // 1 道藤蔓（单股自然螺旋）
vine_height      = 2.0;      // 藤蔓凸出于核心的高度（mm，加粗补偿单股）
vine_width_k     = 1.6;      // 藤蔓 2D 椭圆切向拉伸系数（让它像缠绕的"枝"而非"球"）

// === 段间装配 ===
joint_dia        = 8;        // Φ8 圆柱榫（v4 比 v3 更细，更精致）
joint_len        = 7;

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
    // 7. 收颈（短直段，承接螺旋杖身）
    : z <  collar_z_top               ? collar_dia
    : z <  collar_z_top + 4           ? lerp(collar_dia, spiral_root_dia, (z-collar_z_top)/4)
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
    for (zr = [band_z_top + 1.5, knot_z_top - 1.5])
        rotate_extrude($fn = 96)
            translate([knot_dia_max/2 - 0.5, zr, 0])
                square([0.6, 0.6]);
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

// ====== 内部空腔（电子腔 + 走线通道 + 各开口） ==============================
module wand_cavity() {
    union() {
        // 1. 电子腔（圆柱）— 藏在手柄内
        translate([0, 0, cavity_z_start])
            cylinder(h = cavity_len, d = cavity_id, $fn = 64);

        // 2. 走线通道（cavity 顶 → 杖尖前 5 mm）
        translate([0, 0, cavity_z_start + cavity_len])
            cylinder(h = total_length - cavity_z_start - cavity_len - 5,
                     d = 2.5, $fn = 24);

        // 3. USB-C 开口（PCB 端 +X 侧，靠近铜环上方便插拔）
        translate([0, 0, cavity_z_pcb + 8])
            rotate([0, 90, 0])
                cube([4, 9, 30], center = true);

        // 4. 用户按键孔（PCB 中段 +Y 侧）
        translate([0, 0, cavity_z_pcb + 18])
            rotate([90, 0, 0])
                cylinder(h = 30, d = 4, $fn = 24, center = true);

        // 5. 状态 LED 窗口（PCB 上段 -X 侧）
        translate([0, 0, cavity_z_pcb + 28])
            rotate([0, -90, 0])
                cylinder(h = 30, d = 2.2, $fn = 24, center = true);

        // 6. 电源开关方孔（手柄底部 -Y 侧，靠近 pommel / 电池端）
        translate([0, 0, cavity_z_batt + 4])
            rotate([90, 0, 0])
                cube([6, 3, 30], center = true);

        // 7. Pommel 内部 M6 攻丝孔（Pommel 旋盖访问电池）
        translate([0, 0, -0.1])
            cylinder(h = 6, d = 6, $fn = 32);
    }
}

// ====== 完整魔杖（中空）====================================================
module wand_full() {
    difference() {
        wand_solid();
        wand_cavity();
    }
}

// ====== PCB / 电池占位（PREVIEW 用） ========================================
module preview_payload() {
    // PCB 竖立（长边 35mm 沿 Z 轴，宽 25mm 沿 X 轴）
    color("forestgreen", 0.85)
        translate([0, 0, cavity_z_pcb + pcb_l/2])
            cube([pcb_w, pcb_t, pcb_l], center = true);
    // 电池竖立（长边 40mm 沿 Z 轴，宽 30mm 沿 X 轴，厚 6mm 沿 Y 轴）
    color("orange", 0.9)
        translate([0, 0, cavity_z_batt + batt_l/2])
            cube([batt_w, batt_t, batt_l], center = true);
}

// ====== 段间装配 =============================================================
module joint_male(z) {
    translate([0, 0, z])
        cylinder(h = joint_len, d = joint_dia, $fn = 32);
}
module joint_female(z) {
    translate([0, 0, z - 0.1])
        cylinder(h = joint_len + 0.2, d = joint_dia + 0.4, $fn = 32);
}

// ====== 段 D：Pommel 铜帽（独立旋盖） =======================================
module part_pommel() {
    difference() {
        pommel_module();
        // 中心 M6 自攻丝孔（旋入手柄底部）
        translate([0, 0, -0.1])
            cylinder(h = pommel_z_top + 0.2, d = 5.2, $fn = 32);
    }
}

// ====== 段 A：Handle 手柄段（z = pommel_z_top .. handle_z_top） ==============
module part_handle() {
    union() {
        difference() {
            intersection() {
                wand_full();
                translate([-50, -50, pommel_z_top])
                    cube([100, 100, handle_z_top - pommel_z_top]);
            }
            // 底部 Pommel 螺孔（接 part_pommel）
            translate([0, 0, pommel_z_top - 0.1])
                cylinder(h = 5.2, d = 5.5, $fn = 32);
        }
        joint_male(handle_z_top);
    }
}

// ====== 段 B：Decor 雕花段（z = handle_z_top .. collar_z_top） ===============
module part_decor() {
    union() {
        difference() {
            intersection() {
                wand_full();
                translate([-50, -50, handle_z_top])
                    cube([100, 100, collar_z_top + 4 - handle_z_top]);
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

// ====== 主入口 ==============================================================
module render_part(p = PART) {
    if      (p == "A")        color("saddlebrown")  part_handle();
    else if (p == "B")        color("saddlebrown")  part_decor();
    else if (p == "C")        color("saddlebrown")  part_shaft();
    else if (p == "D")        color("darkgoldenrod") part_pommel();
    else if (p == "PREVIEW")  {
        color("saddlebrown") wand_full();
        preview_payload();
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
