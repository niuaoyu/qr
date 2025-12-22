# c:\Users\nay\Desktop\qr\qr\worldquant\clean_new_alphas.py

import os
import re

def is_header_line(line: str) -> bool:
    """
    检查某一行是否属于文件头部分。
    文件头行被定义为空行、分隔符行，或包含特定元数据键的行。
    """
    stripped_line = line.strip()
    if not stripped_line:  # 如果是空行，视作文件头的一部分
        return True
    
    # 定义文件头行的正则表达式模式
    header_patterns = [
        r'^--------------------------------------------------$',
        r'^Alpha ID:',
        r'^Expression:',
        r'^Sharpe:',
        r'^Turnover:',
        r'^Fitness:',
        r'^Grade:',
        r'^Status:',
        r'^Reason:'
    ]
    
    for pattern in header_patterns:
        if re.match(pattern, stripped_line):
            return True
            
    return False

def remove_duplicates_from_new_file(directory_path, new_file_name):
    """
    扫描一个目录中的所有.txt文件以构建一个现有行的“数据集”。
    然后，它会读取一个指定的“新”文件，智能跳过文件头，
    并删除内容部分中在数据集中已存在的行，以及文件内部的重复行。
    最后用唯一的行覆盖新文件。

    Args:
        directory_path (str): 包含文本文件的目录路径。
        new_file_name (str): 需要清理的新文件名。
    """
    new_file_path = os.path.join(directory_path, new_file_name)
    
    if not os.path.exists(new_file_path):
        print(f"错误：新文件 '{new_file_path}' 不存在。")
        return

    # --- 1. 从所有其他文件中构建旧数据集 (智能跳过文件头) ---
    print("🔍 正在从旧文件中构建数据集...")
    old_lines_set = set()
    try:
        # 遍历目录下的所有文件
        for filename in os.listdir(directory_path):
            # 确保是txt文件，并且不是我们正在处理的新文件
            if filename.endswith('.txt') and filename != new_file_name:
                current_file_path = os.path.join(directory_path, filename)
                print(f"  - 正在读取: {filename}")
                with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    is_content_started_old = False
                    for line in f:
                        # 跳过旧文件的文件头
                        if not is_content_started_old and is_header_line(line):
                            continue
                        else:
                            is_content_started_old = True
                            stripped_line = line.strip()
                            if stripped_line:  # 忽略空行
                                old_lines_set.add(stripped_line)
    except Exception as e:
        print(f"构建数据集时出错: {e}")
        return
        
    print(f"✅ 数据集构建完成，共包含 {len(old_lines_set)} 条独一无二的旧数据。")
    print("-" * 50)

    # --- 2. 读取新文件，分离文件头和内容，并去重 ---
    print(f"📄 正在处理新文件: {new_file_name}")
    header_lines = []
    unique_content_lines = []
    original_lines = []
    duplicate_count = 0
    
    try:
        with open(new_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_lines = f.readlines()

        is_content_started_new = False
        for line in original_lines:
            # 分离文件头和内容
            if not is_content_started_new and is_header_line(line):
                header_lines.append(line)
            else:
                # 内容部分开始
                is_content_started_new = True
                stripped_line = line.strip()
                
                # 如果行是空的，直接保留
                if not stripped_line:
                    unique_content_lines.append(line)
                    continue

                # 检查是否重复 (对旧文件+对自身)
                if stripped_line in old_lines_set:
                    duplicate_count += 1
                    print(f"  - 发现重复行，将删除: {stripped_line[:80]}...")
                else:
                    # 保留原始行，并将此行加入集合以用于后续的自清洁检查
                    unique_content_lines.append(line)
                    old_lines_set.add(stripped_line)
    except Exception as e:
        print(f"处理新文件时出错: {e}")
        return

    # --- 3. 将独有的行写回新文件 ---
    try:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.writelines(header_lines)
            f.writelines(unique_content_lines)
    except Exception as e:
        print(f"写回文件时出错: {e}")
        return

    # --- 4. 打印总结 ---
    final_content_count = sum(1 for line in unique_content_lines if line.strip())
    original_content_count = sum(1 for line in original_lines if not is_header_line(line) and line.strip())

    print("-" * 50)
    print("🎉 处理完成！")
    print(f"原始总行数: {len(original_lines)}")
    print(f"原始内容行数: {original_content_count}")
    print(f"发现并删除的重复内容行数: {duplicate_count}")
    print(f"清理后剩余独有内容行数: {final_content_count}")
    print(f"✅ 文件 '{new_file_path}' 已被更新。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 定义你的文件路径
    DIRECTORY = r'C:\Users\nay\Desktop\qr\qr\worldquant\ready_to_test_alpha_list\clean_alpha'
    NEW_FILE = r'C:\Users\nay\Desktop\qr\qr\worldquant\ready_to_test_alpha_list\test9_gpt.txt'
    
    remove_duplicates_from_new_file(DIRECTORY, NEW_FILE)
