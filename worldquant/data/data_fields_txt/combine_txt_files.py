import os
from os.path import expanduser

def combine_txt_files():
    # 定义源目录和输出文件路径
    source_dir = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\data_fields_txt")
    output_file = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\combined_data_fields.txt")

    if not os.path.exists(source_dir):
        print(f"❌ 源目录不存在: {source_dir}")
        return

    print(f"📂 开始合并目录下的 TXT 文件: {source_dir}")
    print(f"📄 目标文件: {output_file}")
    
    count = 0
    # 使用 'w' 模式打开输出文件，如果文件已存在则覆盖
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 遍历目录
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    
                    try:
                        # 1. 写入文件名标题
                        outfile.write(f"=== 文件名: {file} ===\n")
                        
                        # 2. 读取源文件内容并写入
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(content)
                        
                        # 3. 写入分隔线 (换行 + 分割线 + 换行)
                        outfile.write("\n" + "="*100 + "\n\n")
                        
                        print(f"  ✅ 已合并: {file}")
                        count += 1
                    except Exception as e:
                        print(f"  ❌ 读取失败 {file}: {e}")

    print(f"\n🎉 合并完成! 共合并 {count} 个文件。")

if __name__ == "__main__":
    combine_txt_files()