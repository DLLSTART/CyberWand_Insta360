// CyberWand v21.0 - 手柄外壳 OpenSCAD 模型
// 用于 3D 打印的 STL 文件生成

// 参数设置
handle_length = 12;        // 手柄长度 mm
handle_outer_diameter = 22; // 手柄外径 mm
handle_inner_diameter = 19; // 手柄内径 mm（容纳 PCB）
wall_thickness = 1.5;       // 壁厚 mm

// 装饰环参数
ring_diameter = handle_outer_diameter * 1.05;
ring_width = 3;
ring_position = 2;  // 距底部距离 mm

// USB-C 开孔参数
usb_hole_width = 8;
usb_hole_height = 4;

// 按键开孔参数
button_hole_diameter = 6;
button_positions = [3, 6, 9];  // 距底部距离 mm

// 螺纹参数（连接杖身）
thread_diameter = 10;
thread_length = 5;

$fn = 64;  // 圆滑度

// 模块：手柄主体（中空圆柱）
module handle_body() {
    difference() {
        // 外圆柱
        cylinder(h = handle_length, d = handle_outer_diameter);
        // 内圆柱（中空）
        translate([0, 0, -1])
            cylinder(h = handle_length + 2, d = handle_inner_diameter);
    }
}

// 模块：装饰环
module decorative_ring() {
    translate([0, 0, ring_position])
        difference() {
            cylinder(h = ring_width, d = ring_diameter);
            translate([0, 0, -1])
                cylinder(h = ring_width + 2, d = handle_inner_diameter);
        }
}

// 模块：USB-C 开孔
module usb_hole() {
    translate([0, 0, -1])
        cube([usb_hole_width, usb_hole_height, handle_length + 2], center = true);
}

// 模块：按键开孔
module button_holes() {
    for (pos = button_positions) {
        rotate([0, 0, 60 * (button_positions[0] == pos ? 0 : 
                           button_positions[1] == pos ? 1 : 2)])
            translate([handle_outer_diameter/2 - 0.5, 0, pos])
                rotate([90, 0, 0])
                    cylinder(h = handle_outer_diameter, d = button_hole_diameter);
    }
}

// 模块：内螺纹（连接杖身）
module internal_thread() {
    translate([0, 0, handle_length - thread_length])
        difference() {
            cylinder(h = thread_length + 1, d = thread_diameter + 1);
            // 简化螺纹（实际需更精细）
            for (i = [0:5]) {
                rotate([0, 0, i * 60])
                    translate([thread_diameter/2 - 0.3, 0, i * 0.8])
                        cube([1, 2, 0.5]);
            }
        }
}

// 模块：底部凹槽（防滑）
module bottom_grip() {
    translate([0, 0, -0.5])
        difference() {
            cylinder(h = 1, d = handle_outer_diameter);
            for (i = [0:8]) {
                rotate([0, 0, i * 45])
                    translate([handle_outer_diameter/2 - 1, 0, 0])
                        cylinder(h = 1.5, d = 2);
            }
        }
}

// 主模型：手柄外壳
module handle_v21() {
    difference() {
        union() {
            // 手柄主体
            handle_body();
            // 装饰环
            decorative_ring();
            // 底部防滑
            bottom_grip();
        }
        union() {
            // USB-C 开孔
            usb_hole();
            // 按键开孔
            button_holes();
            // 内螺纹
            internal_thread();
        }
    }
}

// 生成模型
handle_v21();

// 注释：导出 STL 命令
// openscad -o handle_v21.stl handle_v21.scad
