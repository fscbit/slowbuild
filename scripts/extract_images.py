import os

# 获取当前工作目录
directory = os.getcwd()

# 图片后缀
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}

file_names = []

# 遍历当前目录及其子目录
for root, dirs, files in os.walk(directory):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in IMAGE_EXTS:
            # 完整文件路径
            file_path = os.path.join(root, file)
            file_names.append(file_path)

# 打印所有图片文件名
print(f"找到 {len(file_names)} 张图片：")
for name in file_names:
    print(name)

# 同时保存到文本文件
output_file = os.path.join(directory, "图片文件列表.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    for name in file_names:
        f.write(name + '\n')
print(f"\n已保存到: {output_file}")
