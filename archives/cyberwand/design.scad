// CyberWand v3.0 - 3D 外壳设计 (OpenSCAD)
// 手持魔杖形态，35×25×8mm

// 参数
length = 35;      // 长度 mm
width = 25;       // 宽度 mm
height = 8;       // 高度 mm
wall_thickness = 1.5;  // 壁厚 mm

// 外壳主体 (流线型设计)
module main_body() {
    difference() {
        // 外形 (圆角长方体)
        hull() {
            translate([length/2 - 5, 0, 0])
                cylinder(h = height, r = width/2, center = true, $fn = 50);
            translate([-length/2 + 5, 0, 0])
                cylinder(h = height, r = width/2, center = true, $fn = 50);
        }
        
        // 内部挖空 (容纳 PCB 和电池)
        hull() {
            translate([length/2 - 5 - wall_thickness, 0, 0.5])
                cylinder(h = height, r = width/2 - wall_thickness, center = true, $fn = 50);
            translate([-length/2 + 5 + wall_thickness, 0, 0.5])
                cylinder(h = height, r = width/2 - wall_thickness, center = true, $fn = 50);
        }
    }
}

// 底部盖子
module bottom_cap() {
    difference() {
        // 外形
        hull() {
            translate([length/2 - 3, 0, -height/2 - 1])
                cylinder(h = 2, r = width/2 + 0.5, center = true, $fn = 50);
            translate([-length/2 + 3, 0, -height/2 - 1])
                cylinder(h = 2, r = width/2 + 0.5, center = true, $fn = 50);
        }
        
        // 卡扣槽
        hull() {
            translate([length/2 - 3 - wall_thickness, 0, -height/2 - 1.5])
                cylinder(h = 2, r = width/2 - wall_thickness + 1, center = true, $fn = 50);
            translate([-length/2 + 3 + wall_thickness, 0, -height/2 - 1.5])
                cylinder(h = 2, r = width/2 - wall_thickness + 1, center = true, $fn = 50);
        }
    }
}

// 按键孔 (顶部左侧)
module button_hole() {
    translate([-length/2 + 6, 0, height/2])
        cylinder(h = height, d = 6, center = true);
}

// LED 窗口 (顶部右侧)
module led_window() {
    translate([length/2 - 6, 0, height/2])
        cylinder(h = height, d = 2, center = true);
}

// USB-C 开口 (底部)
module usb_c_cutout() {
    translate([0, 0, -height/2])
        cube([8, 10, 4], center = true);
}

// 挂绳孔 (可选)
module lanyard_hole() {
    translate([-length/2 + 4, 0, 0])
        rotate([90, 0, 0])
            cylinder(h = width, d = 3, center = true);
}

// 完整组装
module assembly() {
    difference() {
        union() {
            main_body();
            bottom_cap();
        }
        
        // 开口
        button_hole();
        led_window();
        usb_c_cutout();
        // lanyard_hole(); // 可选
    }
}

// 握持区域纹理
module grip_texture() {
    for (i = [-10:3:10]) {
        translate([i, width/2 + 0.5, 0])
            rotate([90, 0, 0])
                cylinder(h = 2, d = 1, center = true);
    }
}

// 渲染
color("darkgray")
    assembly();

// 导出说明
// 1. 导出为 STL: main_body.stl, bottom_cap.stl
// 2. 3D 打印材料：TPU 软胶 (握持舒适) 或 PLA+
// 3. 填充率：30% (增加强度)
// 4. 层厚：0.15mm (精细)
// 5. 支撑：需要 (USB-C 开口处)
// 6. 打印方向：底部朝下
