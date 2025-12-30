import os
import re

def main():
    # 定义要扫描的根目录
    base_dir = r"C:\qr\qr\worldquant\result"
    # 定义输出文件名
    output_filename = "all_extracted_ids.txt"
    output_path = os.path.join(base_dir, output_filename)
    
    # 使用集合来存储ID，自动去重
    unique_ids = set()
    
    print(f"开始扫描目录: {base_dir}")

    # 遍历目录及其子目录
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # 只处理txt文件，并且跳过输出文件本身以防死循环
            if file.endswith(".txt") and file != output_filename:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # 正则表达式：匹配 "Alpha ID:" 后面的空白字符，然后捕获8个字母或数字
                        ids = re.findall(r"Alpha ID:\s*([a-zA-Z0-9]{8})", content)
                        if ids:
                            unique_ids.update(ids)
                            print(f"  -> 从文件 {file} 中提取了 {len(ids)} 个 ID")
                except Exception as e:
                    print(f"  [!] 读取文件 {file} 时出错: {e}")

    # 将结果写入文件
    if unique_ids:
        sorted_ids = sorted(list(unique_ids))
        with open(output_path, 'w', encoding='utf-8') as f:
            for alpha_id in sorted_ids:
                f.write(f"{alpha_id}\n")
        print(f"\n提取完成！共找到 {len(unique_ids)} 个唯一的 Alpha ID。")
        print(f"结果已保存至: {output_path}")
    else:
        print("\n未找到任何 Alpha ID。")

if __name__ == "__main__":
    main()
