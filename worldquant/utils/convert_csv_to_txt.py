import os
import pandas as pd
from os.path import expanduser

def convert_all_csv_to_txt():
    # 定义数据所在的根目录
    data_fields_dir = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\data_fields")
    base_dir = os.path.dirname(data_fields_dir)
    output_dir = os.path.join(base_dir, "data_fields_txt")

    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 已创建输出目录: {output_dir}")

    print(f"📂 开始遍历目录: {base_dir}")
    print("🔄 正在将 CSV 转换为 TXT (使用 Tab 分隔)...")

    count = 0
    # os.walk 会递归遍历所有子目录 (例如 TOPSP500, TOP3000 等)
    for root, dirs, files in os.walk(data_fields_dir):
        for file in files:
            if file.endswith(".csv"):
                csv_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, data_fields_dir)
                txt_dir = os.path.join(output_dir, relative_path)
                if not os.path.exists(txt_dir):
                    os.makedirs(txt_dir)

                parent_name = os.path.basename(root)
                txt_path = os.path.join(txt_dir, f"{parent_name}_{file.replace('.csv', '.txt')}")

                try:
                    # 读取 CSV
                    df = pd.read_csv(csv_path)

                    # 保存为 TXT
                    # sep='\t' 表示使用制表符分隔，index=False 表示不保存行索引
                    df.to_csv(txt_path, sep='\t', index=False)

                    print(f"  ✅ 转换成功: {file} -> {os.path.basename(txt_path)}")
                    count += 1
                except Exception as e:

                    print(f"  ❌ 转换失败 {file}: {e}")

    print(f"\n🎉 全部完成! 共转换了 {count} 个文件。")

if __name__ == "__main__":
    convert_all_csv_to_txt()
