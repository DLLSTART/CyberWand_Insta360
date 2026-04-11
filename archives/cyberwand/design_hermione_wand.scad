// CyberWand v3.1 - 赫敏魔杖风格设计 (OpenSCAD)
// 参考哈利波特赫敏魔杖造型

// 参数
wand_length = 35;       // 魔杖长度 mm
wand_width = 25;        // 最大宽度 mm
wand_height = 8;        // 高度 mm

// 高质量渲染设置
$fa = 0.5;
$fs = 0.1;

// 装饰球节点（赫敏魔杖特色）
module decorative_sphere(x_pos, radius, texture = true) {
    translate([x_pos, 0, 0]) {
        if (texture) {
            // 蜂窝状纹理
            difference() {
                sphere(r = radius, $fn = 50);
                // 创建蜂窝孔
                for (i = [0:60:360]) {
                    for (j = [-30, 0, 30]) {
                        rotate([j, i, 0])
                            translate([radius - 0.5, 0, 0])
                                cylinder(h = radius * 2, r = 0.8, $fn = 20);
                    }
                }
            }
        } else {
            sphere(r = radius, $fn = 50);
        }
    }
}

// 杖身主体（细长型）
module wand_shaft() {
    // 主杖身（细圆柱）
    cylinder(h = wand_length, r1 = 2.5, r2 = 3.5, $fn = 50);
}

// 赫敏风格魔杖主体
module hermione_wand_body() {
    difference() {
        union() {
            // 1. 主杖身（细长圆柱）
            translate([-wand_length/2 + 2, 0, 0])
                cylinder(h = wand_length - 4, r = 2, $fn = 50);
            
            // 2. 手柄底部（球形）
            translate([wand_length/2 - 3, 0, 0])
                sphere(r = 3.5, $fn = 50);
            
            // 3. 装饰球节点（赫敏风格 - 5 个球）
            decorative_sphere(wand_length/2 - 8, 3.2, true);
            decorative_sphere(wand_length/2 - 13, 3.0, true);
            decorative_sphere(wand_length/2 - 18, 2.8, true);
            decorative_sphere(wand_length/2 - 23, 2.6, true);
            decorative_sphere(wand_length/2 - 28, 2.4, true);
            
            // 4. 杖尖（细锥形）
            translate([-wand_length/2 + 2, 0, 0])
                cylinder(h = 8, r1 = 1, r2 = 2, $fn = 50);
        }
        
        // 内部挖空（容纳电子元件）
        translate([wand_length/2 - 5, 0, 0])
            cylinder(h = 15, r = 2.5, $fn = 50);
    }
}

// 按键孔（手柄顶部）
module button_hole() {
    translate([wand_length/2 - 5, 0, 4])
        sphere(r = 2.5, $fn = 30);
}

// LED 窗口（杖尖发光）
module led_window() {
    translate([-wand_length/2 + 4, 0, 0])
        sphere(r = 1, $fn = 30);
}

// USB-C 开口（手柄底部）
module usb_c_cutout() {
    translate([wand_length/2 + 2, 0, -3])
        cube([5, 7, 3], center = true);
}

// 完整魔杖组装
module hermione_wand_assembly() {
    difference() {
        hermione_wand_body();
        
        // 功能开口
        button_hole();
        led_window();
        usb_c_cutout();
    }
}

// 渲染 - 深红木色
color("#8B4513")
    hermione_wand_assembly();

// 导出说明
// 1. 导出为 STL: hermione_wand.stl
// 2. 3D 打印材料：PLA Wood 或 红木色 PLA
// 3. 填充率：25%
// 4. 层厚：0.12mm（超精细，展现纹理）
// 5. 支撑：需要（悬空装饰球）
// 6. 打印方向：对角线放置（45 度角）
// 7. 后处理：打磨 + 深色蜡抛光

// 设计特点
// - 赫敏魔杖风格：多个装饰球节点
// - 蜂窝状纹理：每个球体有雕刻纹理
// - 细长杖身：优雅比例
// - 功能集成：隐藏式按键、LED、USB-C
