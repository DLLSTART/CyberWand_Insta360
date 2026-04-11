// CyberWand 高质量渲染脚本 (OpenSCAD)
// 保存为 render_wand_hd.scad

// 高质量渲染设置
$fa = 0.5;  // 最小片段角度（更小的值 = 更光滑）
$fs = 0.1;   // 最小片段尺寸（更小的值 = 更光滑）

// 魔杖参数
wand_length = 35;
wand_width = 25;
wand_height = 8;

// 圆环辅助模块
module torus(r, r_tube, $fn = 100) {
    rotate_extrude($fn = $fn)
        translate([r, 0, 0])
            circle(r = r_tube, $fn = $fn/4);
}

// 魔杖主体（高质量）
module wand_body_hq() {
    difference() {
        union() {
            // 手柄部分
            translate([wand_length/2 - 8, 0, 0])
                scale([1, 1, 0.8])
                    sphere(r = wand_width/2, $fn = 100);
            
            // 杖身部分
            hull() {
                translate([wand_length/2 - 8, 0, 0])
                    scale([1, 1, 0.8])
                        sphere(r = wand_width/2 - 2, $fn = 100);
                translate([-wand_length/2 + 5, 0, 0])
                    scale([1, 1, 0.6])
                        sphere(r = wand_width/3, $fn = 100);
            }
            
            // 杖尖
            translate([-wand_length/2 + 3, 0, 0])
                scale([1, 1, 0.5])
                    sphere(r = wand_width/4, $fn = 100);
        }
        
        // 内部挖空
        hull() {
            translate([wand_length/2 - 8, 0, 1])
                sphere(r = wand_width/2 - 2.5, $fn = 100);
            translate([-wand_length/2 + 8, 0, 1])
                sphere(r = wand_width/4 - 1, $fn = 100);
        }
    }
}

// 完整魔杖
module wand_full() {
    difference() {
        wand_body_hq();
        
        // 按键孔
        translate([wand_length/2 - 3, 0, wand_height/2])
            sphere(r = 3, $fn = 50);
        
        // LED 窗口
        translate([-wand_length/2 + 2, 0, 0])
            sphere(r = 1.5, $fn = 50);
        
        // USB-C 开口
        translate([wand_length/2 + 2, 0, -wand_height/2])
            cube([6, 8, 4], center = true);
    }
}

// 渲染
color("darkbrown")
    wand_full();

// 使用说明：
// 命令行渲染：
// openscad -o output.png --imgsize=1920,1080 --projection=o --viewall -D 'wand_full()' design_harry_potter.scad
