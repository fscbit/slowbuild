# 按日期拆分Excel表格
# 用法：把Excel文件放到脚本同目录，运行后自动按第3列日期拆分
import os
import pandas as pd

# 自动找当前目录第一个Excel文件
files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]
if not files:
    print("错误：当前目录没有找到Excel文件！")
    input("按回车退出...")
    exit()

input_file = files[0]
print(f"读取文件: {input_file}")

df = pd.read_excel(input_file)

# 尝试解析第3列（索引2）为日期
try:
    df['_日期'] = pd.to_datetime(df.iloc[:, 2], errors='coerce').dt.date
except:
    print(f"错误：第3列不是日期格式！")
    input("按回车退出...")
    exit()

valid = df.dropna(subset=['_日期'])
print(f"共 {len(valid)} 行有效数据，按日期拆分中...")

count = 0
for date_val in valid['_日期'].unique():
    day_df = valid[valid['_日期'] == date_val]
    if not day_df.empty:
        filename = str(date_val).replace(':', '_') + '.xlsx'
        day_df.drop(columns=['_日期']).to_excel(filename, index=False)
        count += 1
        print(f"已生成: {filename} ({len(day_df)} 行)")

print(f"\n完成！共生成 {count} 个文件。")
input("按回车退出...")
