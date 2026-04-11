"""
CyberWand - 精确还原图片中的魔杖设计
使用 Blender Python API 进行专业建模
"""

import bpy
import math

# 清除默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 魔杖参数（根据图片比例）
wand_length = 35.0      # 总长度 mm
wand_diameter = 2.5     # 杖身直径 mm

# 创建魔杖主体（细圆柱）
bpy.ops.mesh.primitive_cylinder_add(
    radius=wand_diameter/2,
    depth=wand_length,
    location=(0, 0, 0),
    rotation=(math.radians(90), 0, 0)
)
wand_body = bpy.context.object
wand_body.name = "Wand_Body"

# 添加 6 个装饰节点（根据图片精确位置）
node_data = [
    {"pos": 25.0, "radius": 2.8, "length": 4.0},   # 节点 1（靠近手柄）
    {"pos": 19.0, "radius": 2.6, "length": 3.8},   # 节点 2
    {"pos": 13.0, "radius": 2.4, "length": 3.5},   # 节点 3
    {"pos": 7.0, "radius": 2.2, "length": 3.2},    # 节点 4
    {"pos": 1.0, "radius": 2.0, "length": 2.8},    # 节点 5
    {"pos": -5.0, "radius": 1.8, "length": 2.5},   # 节点 6（靠近杖尖）
]

nodes = []
for i, node in enumerate(node_data):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=node["radius"],
        minor_radius=node["length"]/2,
        location=(node["pos"], 0, 0),
        rotation=(math.radians(90), 0, 0)
    )
    node_obj = bpy.context.object
    node_obj.name = f"Node_{i+1}"
    nodes.append(node_obj)

# 创建手柄（球形设计）
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=3.5,
    location=(17.5, 0, 0)
)
handle = bpy.context.object
handle.name = "Handle"

# 创建杖尖（细锥形）
bpy.ops.mesh.primitive_cone_add(
    radius1=0.5,
    radius2=1.2,
    depth=6.0,
    location=(-17.5, 0, 0),
    rotation=(math.radians(180), 0, 0)
)
tip = bpy.context.object
tip.name = "Tip"

# 合并所有部件
bpy.ops.object.select_all(action='DESELECT')
wand_body.select_set(True)
for node in nodes:
    node.select_set(True)
handle.select_set(True)
tip.select_set(True)

bpy.context.view_layer.objects.active = wand_body
bpy.ops.object.join()

# 添加布尔运算创建内部空腔
bpy.ops.mesh.primitive_cylinder_add(
    radius=2.0,
    depth=20.0,
    location=(12.0, 0, 0),
    rotation=(math.radians(90), 0, 0)
)
cavity = bpy.context.object
cavity.name = "Cavity"

# 设置为布尔切割
bpy.ops.object.select_all(action='DESELECT')
wand_body.select_set(True)
cavity.select_set(True)
bpy.context.view_layer.objects.active = cavity

# 添加按键孔
bpy.ops.mesh.primitive_sphere_add(
    radius=1.5,
    location=(15.0, 0, 3.0)
)
button_cut = bpy.context.object
button_cut.name = "Button_Cut"

# 添加 LED 窗口
bpy.ops.mesh.primitive_sphere_add(
    radius=0.8,
    location=(-14.0, 0, 0)
)
led_cut = bpy.context.object
led_cut.name = "LED_Cut"

# 添加 USB-C 开口
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(18.0, 0, -2.0)
)
usb_cut = bpy.context.object
usb_cut.name = "USB_Cut"
usb_cut.scale = (4.0, 3.0, 2.0)

# 设置材质（深红木色）
material = bpy.data.materials.new(name="Dark_Wood")
material.use_nodes = True
bsdf = material.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.42, 0.24, 0.12, 1.0)  # #6B3E1F
bsdf.inputs["Roughness"].default_value = 0.6
bsdf.inputs["Specular IOR Level"].default_value = 0.3

wand_body.data.materials.append(material)

# 设置渲染
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128
bpy.context.scene.render.resolution_x = 2560
bpy.context.scene.render.resolution_y = 1440
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = "D:/workspace/CyberWand_Insta360/enclosure/classic_wand_blender.png"

# 设置相机
bpy.ops.object.camera_add(location=(0, -50, 30), rotation=(math.radians(75), 0, 0))
camera = bpy.context.object
bpy.context.scene.camera = camera

# 设置灯光
bpy.ops.object.light_add(type='SUN', location=(20, -30, 40))
sun = bpy.context.object
sun.data.energy = 3.0

bpy.ops.object.light_add(type='AREA', location=(-20, 30, 20))
area = bpy.context.object
area.data.energy = 100.0
area.data.size = 5.0

# 渲染
bpy.ops.render.render(write_still=True)

print("✅ Blender 渲染完成！")
