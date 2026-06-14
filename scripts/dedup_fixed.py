import os
import glob
import filecmp

dir_path = os.getcwd()
print(f"正在扫描: {dir_path}")

file_lst = []
for i in glob.glob(dir_path + '/**/*', recursive=True):
    if os.path.isfile(i):
        file_lst.append(i)

removed = 0
for x in file_lst:
    for y in file_lst:
        if x != y and os.path.exists(x) and os.path.exists(y):
            if filecmp.cmp(x, y):
                os.remove(y)
                print(f"已删除重复: {os.path.basename(y)}")
                removed += 1

print(f"\n去重完成！共删除 {removed} 个重复文件。")
input("按回车退出...")
