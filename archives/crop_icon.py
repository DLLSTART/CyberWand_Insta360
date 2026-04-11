# 裁剪魔杖图片为应用图标
from PIL import Image
import os

# 选择最合适的图片（v39 椭圆节点设计，经典优雅）
input_image = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v39_ellipsoid.png"
output_icon = r"D:\workspace\CyberWand_Insta360\host_program\feishu_bot\app_icon.png"

# 打开图片
img = Image.open(input_image)
print(f"原图尺寸：{img.size[0]} x {img.size[1]}")

# 计算正方形裁剪区域（居中裁剪）
width, height = img.size
min_dim = min(width, height)
left = (width - min_dim) // 2
top = (height - min_dim) // 2
right = left + min_dim
bottom = top + min_dim

print(f"裁剪区域：({left}, {top}) 到 ({right}, {bottom})")

# 裁剪
cropped = img.crop((left, top, right, bottom))

# 缩放到 240x240（飞书要求 > 240px）
icon_size = (512, 512)  # 使用更大的尺寸以确保质量
resized = cropped.resize(icon_size, Image.Resampling.LANCZOS)

# 保存
resized.save(output_icon, "PNG", quality=95)
print("Icon saved: " + output_icon)
print("Icon size: " + str(resized.size[0]) + " x " + str(resized.size[1]))

# 验证文件大小
file_size = os.path.getsize(output_icon)
print("File size: " + str(round(file_size / 1024, 1)) + " KB")
