// CyberWand v3.2 - 哈利波特经典魔杖风格 (OpenSCAD)
// 参考图片：6-7 个装饰节点，蜂窝纹理，深红木色

// 参数
wand_length = 35;       // 魔杖长度 mm
wand_diameter = 3;      // 杖身直径 mm
node_count = 6;         // 装饰节点数量

// 高质量渲染设置
$fa = 0.5;
$fs = 0.1;

// 装饰节点（蜂窝纹理）
module decorative_node(x_pos, node_radius, node_length) {
    translate([x_pos, 0, 0]) {
        difference() {
            // 节点主体（球状）
            hull() {
                sphere(r = node_radius, $fn = 60);
                translate([0, 0, node_length/2])
                    sphere(r = node_radius * 0.9, $fn = 60);
                translate([0, 0, -node_length/2])
                    sphere(r = node_radius * 0.9, $fn = 60);
            }
            
            // 蜂窝纹理（凹陷）
            for (i = [0:45:360]) {
                for (j = [-20, 0, 20]) {
                    rotate([j, i, 0])
                        translate([node_radius - 0.3, 0, 0])
                            cylinder(h = node_radius, r = 0.6, $fn = 15);
                }
            }
        }
    }
}

// 杖身主体（细圆柱）
module wand_shaft() {
    cylinder(h = wand_length, r = wand_diameter/2, $fn = 50);
}

// 完整魔杖（参考新图片）
module classic_wand_body() {
    difference() {
        union() {
            // 1. 主杖身（细圆柱）
            translate([0, 0, -wand_length/2])
                cylinder(h = wand_length, r1 = 1.8, r2 = 1.2, $fn = 50);
            
            // 2. 装饰节点（6 个，从手柄到杖尖递减）
            node_positions = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10];
            node_radii = [2.8, 2.6, 2.4, 2.2, 2.0, 1.8];
            node_lengths = [5, 4.5, 4, 3.5, 3, 2.5];
            
            for (i = [0:5]) {
                x_pos = -wand_length/2 + node_positions[i] * wand_length;
                decorative_node(x_pos, node_radii[i], node_lengths[i]);
            }
            
            // 3. 手柄底部（特殊球形设计）
            translate([wand_length/2 - 3, 0, 0]) {
                hull() {
                    sphere(r = 3.5, $fn = 60);
                    translate([2, 0, 0])
                        sphere(r = 2.5, $fn = 60);
                }
            }
            
            // 4. 杖尖（细长锥形）
            translate([-wand_length/2, 0, 0])
                cylinder(h = 8, r1 = 0.5, r2 = 1.2, $fn = 50);
        }
        
        // 内部挖空（容纳电子元件）
        translate([wand_length/2 - 5, 0, 0])
            cylinder(h = 18, r = 2.8, $fn = 50);
    }
}

// 按键孔（手柄顶部，隐藏式）
module button_hole() {
    translate([wand_length/2 - 4, 0, 3.5])
        sphere(r = 2, $fn = 30);
}

// LED 窗口（杖尖发光）
module led_window() {
    translate([-wand_length/2 + 3, 0, 0])
        sphere(r = 0.8, $fn = 30);
}

// USB-C 开口（手柄底部）
module usb_c_cutout() {
    translate([wand_length/2 + 2, 0, -2.5])
        cube([4, 6, 2.5], center = true);
}

// 完整魔杖组装
module classic_wand_assembly() {
    difference() {
        classic_wand_body();
        
        // 功能开口
        button_hole();
        led_window();
        usb_c_cutout();
    }
}

// 渲染 - 深红木色
color("#6B3E1F")
    classic_wand_assembly();

// 导出说明
// 1. 导出为 STL: classic_wand.stl
// 2. 3D 打印材料：PLA Wood 或 红木色 PLA
// 3. 填充率：25%
// 4. 层厚：0.10mm（超精细，展现蜂窝纹理）
// 5. 支撑：需要（悬空装饰节点）
// 6. 打印方向：对角线 45 度角
// 7. 后处理：打磨 + 深色蜡抛光

// 设计特点
// - 6 个装饰节点（蜂窝纹理）
// - 细长杖身（优雅比例）
// - 手柄特殊球形设计
// - 功能集成：隐藏式按键、LED、USB-C
