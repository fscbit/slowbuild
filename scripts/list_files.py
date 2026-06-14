# 文件名列表 → Excel
# 运行后自动导出当前目录所有文件名到Excel表格
import os
import pandas as pd

current_dir = os.getcwd()
print(f"扫描目录: {current_dir}")

file_names = os.listdir(current_dir)
df = pd.DataFrame(file_names, columns=['文件名'])

# 自动生成不重名Excel文件
excel_path = '文件列表.xlsx'
counter = 1
while os.path.exists(excel_path):
    excel_path = f'文件列表{counter}.xlsx'
    counter += 1

df.to_excel(excel_path, index=False)

print(f'✅ 共 {len(file_names)} 个文件，已保存到: {excel_path}')
input("按回车退出...")
