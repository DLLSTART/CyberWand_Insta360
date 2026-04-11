// CyberWand v21.0 - 按键帽 OpenSCAD 模型
// 用于 3D 打印的 STL 文件生成

// 参数设置
button_cap_diameter = 8;   // 按键帽外径 mm
button_cap_height = 4;     // 按键帽高度 mm
button_stem_diameter = 5;  // 按键柱直径 mm
button_stem_height = 2;    // 按键柱高度 mm
button_hole_diameter = 6;  // 适配手柄开孔 mm

// 轻触开关尺寸
switch_height = 3.5;       // 6mm 轻触开关高度

$fn = 64;  // 圆滑度

// 模块：按键帽主体
module button_cap_body() {
    difference() {
        union() {
            // 顶部圆顶
            translate([0, 0, button_stem_height])
                sphere(d = button_cap_diameter);
            // 按键柱
            cylinder(h = button_stem_height, d = button_stem_diameter);
        }
        // 底部凹槽（容纳开关）
        translate([0, 0, -1])
            cylinder(h = switch_height + 2, d = button_stem_diameter + 0.5);
    }
}

// 模块：表面纹理（防滑纹）
module grip_texture() {
    for (i = [0:12]) {
        rotate([0, 0, i * 30])
            translate([button_cap_diameter/2 - 0.3, 0, button_stem_height + 2])
                rotate([90, 0, 0])
                    cylinder(h = button_cap_diameter, d = 0.5);
    }
}

// 主模型：按键帽
module button_cap_v21() {
    difference() {
        button_cap_body();
        // 表面纹理（凹陷）
        grip_texture();
    }
}

// 生成 3 个按键帽（并排）
module button_caps_3x() {
    for (i = [0:2]) {
        translate([i * 12, 0, 0])
            button_cap_v21();
    }
}

// 导出单个按键帽
button_cap_v21();

// 注释：导出 STL 命令
// 单个：openscad -o button_cap_v21.stl button_cap_v21.scad
// 3 个：openscad -o button_caps_3x_v21.stl -D build_3x=true button_cap_v21.scad
