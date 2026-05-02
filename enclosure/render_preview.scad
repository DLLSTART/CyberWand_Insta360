// ============================================================================
//  老魔杖渲染预览（生成 PNG 截图用）
//  通过 include 复用 elder_wand.scad 的全部模块/函数/变量
//  并把魔杖躺平到 X 轴方向便于横向布图
// ============================================================================

include <elder_wand.scad>;
RENDER_TOP_LEVEL = false;   // 覆盖 elder_wand.scad 末尾自动渲染（OpenSCAD "last assignment wins"）

VIEW = "HORIZONTAL";        // HORIZONTAL / ISO / SECTION / TIP_CLOSEUP / POMMEL_CLOSEUP / BAND_CLOSEUP / EXPLODED

// === 剖切：去掉 +Y 半边露出电子腔，并叠加 v5 真实 PCB+元件占位 ===
module section_cut() {
    difference() {
        color("saddlebrown") wand_full();
        translate([-100, 0, -10]) cube([200, 120, total_length + 20]);
    }
    preview_payload();   // 改用 elder_wand.scad 中的 v5 真实占位
}

// === 视图分发 ===
if (VIEW == "HORIZONTAL") {
    rotate([0, 90, 0]) color("saddlebrown") wand_full();
}
else if (VIEW == "EXPLODED") {
    // v4 4 段拆分：D Pommel + A Handle + B Decor + C Shaft
    rotate([0, 90, 0]) {
        // D Pommel（向 -Z 偏移 25 mm）
        translate([0, 0, -25])
            color("darkgoldenrod") part_pommel();
        // A Handle (z = pommel_z_top..handle_z_top)
        color("saddlebrown") part_handle();
        // B Decor (z = handle_z_top..collar_z_top+4)，向 +Z 偏 22 mm
        translate([0, 0, 22])
            color("saddlebrown") part_decor();
        // C Shaft (z = collar_z_top+4..total_length)，再偏 50 mm
        translate([0, 0, 50])
            color("saddlebrown") part_shaft();
    }
}
else if (VIEW == "SECTION") {
    rotate([0, 90, 0]) section_cut();
}
else if (VIEW == "TIP_CLOSEUP") {
    // v4: 杖尖在 z=300..360
    rotate([0, 90, 0])
        intersection() {
            color("saddlebrown") wand_full();
            translate([-30, -30, 280]) cube([60, 60, 90]);
        }
}
else if (VIEW == "POMMEL_CLOSEUP") {
    // v4: pommel + 部分手柄底端 z=0..40
    rotate([0, 90, 0]) {
        color("darkgoldenrod") pommel_module();
        intersection() {
            color("saddlebrown") wand_full();
            translate([-50, -50, pommel_z_top]) cube([100, 100, 40]);
        }
    }
}
else if (VIEW == "BAND_CLOSEUP") {
    // v4: 上铜环 + 鳞纹带 + 雕花结 + 收颈 z=100..170
    rotate([0, 90, 0])
        intersection() {
            color("saddlebrown") wand_full();
            translate([-30, -30, handle_z_top - 5]) cube([60, 60, 75]);
        }
}
else if (VIEW == "ISO") {
    // 经典 3D 轴测视角
    rotate([0, 90, 0]) color("saddlebrown") wand_full();
}
