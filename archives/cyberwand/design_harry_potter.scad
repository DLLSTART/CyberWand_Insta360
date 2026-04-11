// CyberWand v3.0 - 哈利波特风格魔杖外壳设计 (OpenSCAD)
// 灵感来源：哈利波特电影中的经典魔杖造型

// 参数
wand_length = 35;       // 魔杖长度 mm
wand_width = 25;        // 最大宽度 mm
wand_height = 8;        // 高度 mm
grip_texture_depth = 0.5;  // 握持纹理深度

// 魔杖主体（流线型，类似哈利波特魔杖）
module wand_body() {
    difference() {
        union() {
            // 手柄部分（较粗）
            translate([wand_length/2 - 8, 0, 0])
                scale([1, 1, 0.8])
                    sphere(r = wand_width/2, $fn = 50);
            
            // 杖身部分（渐变变细）
            hull() {
                translate([wand_length/2 - 8, 0, 0])
                    scale([1, 1, 0.8])
                        sphere(r = wand_width/2 - 2, $fn = 50);
                translate([-wand_length/2 + 5, 0, 0])
                    scale([1, 1, 0.6])
                        sphere(r = wand_width/3, $fn = 50);
            }
            
            // 杖尖部分（细）
            translate([-wand_length/2 + 3, 0, 0])
                scale([1, 1, 0.5])
                    sphere(r = wand_width/4, $fn = 50);
        }
        
        // 内部挖空（容纳电子元件）
        hull() {
            translate([wand_length/2 - 8, 0, 1])
                sphere(r = wand_width/2 - 2.5, $fn = 50);
            translate([-wand_length/2 + 8, 0, 1])
                sphere(r = wand_width/4 - 1, $fn = 50);
        }
    }
}

// 握持区域纹理（螺旋纹，类似奥利凡德魔杖）
module grip_texture() {
    for (i = [0:15:360]) {
        rotate([0, 0, i])
        translate([wand_length/2 - 5, 0, 0])
            cylinder(h = 10, r = wand_width/2 + 0.3, $fn = 50);
    }
}

// 装饰环（魔杖上的装饰性圆环）
module decorative_rings() {
    for (i = [-5, 0, 5]) {
        translate([wand_length/2 + i, 0, 0])
            rotate([90, 0, 0])
                torus(r = wand_width/2 + 0.5, r_tube = 1, $fn = 50);
    }
}

// 按键孔（顶部，隐藏式设计）
module button_hole() {
    translate([wand_length/2 - 3, 0, wand_height/2])
        sphere(r = 3, $fn = 50);
}

// LED 窗口（杖尖，发光效果）
module led_window() {
    translate([-wand_length/2 + 2, 0, 0])
        sphere(r = 1.5, $fn = 50);
}

// USB-C 开口（底部，隐藏式）
module usb_c_cutout() {
    translate([wand_length/2 + 2, 0, -wand_height/2])
        cube([6, 8, 4], center = true);
}

// 挂绳孔（手柄末端）
module lanyard_hole() {
    translate([wand_length/2 + 5, 0, 0])
        rotate([90, 0, 0])
            cylinder(h = wand_width, r = 1.5, $fn = 50);
}

// 完整魔杖组装
module wand_assembly() {
    difference() {
        union() {
            wand_body();
            // 握持纹理
            // grip_texture(); // 可选，增加摩擦力
            // 装饰环
            // decorative_rings(); // 可选，装饰性
        }
        
        // 功能开口
        button_hole();
        led_window();
        usb_c_cutout();
        // lanyard_hole(); // 可选
    }
}

// 辅助模块：圆环
module torus(r, r_tube, $fn = 50) {
    rotate_extrude($fn = $fn)
        translate([r, 0, 0])
            circle(r = r_tube, $fn = $fn/4);
}

// 渲染
color("darkbrown")  // 魔杖颜色：深棕色
    wand_assembly();

// 导出说明
// 1. 导出为 STL: wand_body.stl
// 2. 3D 打印材料：PLA Wood（木纹 PLA，更有魔杖质感）
// 3. 填充率：25%
// 4. 层厚：0.15mm（精细）
// 5. 支撑：需要（悬空部分）
// 6. 打印方向：水平放置
// 7. 后处理：打磨 + 上色（古铜色/深棕色）

// 设计灵感
// - 哈利波特魔杖：经典、复古、神秘
// - 奥利凡德魔杖：精致、纹理、装饰
// - 现代科技融合：隐藏式按键、LED 灯效
