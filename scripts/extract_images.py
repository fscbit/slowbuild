# 图片文件提取器
# 递归搜索当前目录所有图片，导出路径列表
import os

directory = os.getcwd()
print(f"正在扫描: {directory}")

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
file_names = []

for root, dirs, files in os.walk(directory):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in IMAGE_EXTS:
            file_names.append(os.path.join(root, file))

output_file = os.path.join(directory, "图片文件列表.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    for name in file_names:
        f.write(name + '\n')

print(f"✅ 找到 {len(file_names)} 张图片")
for name in file_names:
    print(f"  {name}")
print(f"\n已保存到: {output_file}")
input("按回车退出...")
