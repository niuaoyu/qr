import os
import re
import sys
# 为了能成功导入 'main_part'，需要将项目的根目录添加到 Python 的搜索路径中。
# 项目根目录 'worldquant' 是当前脚本所在目录 'ready_to_test_alpha_list' 的上一级。
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from qr.worldquant.global_config import DATA_PATH
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

def clean_and_deduplicate_file(file_path: str):
    """
    清理单个TXT文件。它会保留文件头，并对文件内容部分进行去重。
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 文件未找到: {file_path}")
        return
    except Exception as e:
        print(f"❌ 读取文件时出错 {file_path}: {e}")
        return

    header_lines = []
    content_lines = []
    is_content_started = False
    
    # 1. 智能分离文件头和内容
    for line in all_lines:
        if not is_content_started and is_header_line(line):
            header_lines.append(line)
        else:
            # 遇到的第一个非文件头行，标志着内容部分的开始
            is_content_started = True
            content_lines.append(line)

    # 2. 对内容部分进行去重
    seen_expressions = set()
    unique_content_lines = []
    original_content_count = 0
    duplicate_count = 0

    for line in content_lines:
        stripped_line = line.strip()
        if not stripped_line:
            # 保留内容区域的空行
            unique_content_lines.append(line)
            continue
        
        original_content_count += 1
        if stripped_line not in seen_expressions:
            seen_expressions.add(stripped_line)
            unique_content_lines.append(line) # 保留原始行以维持格式
        else:
            duplicate_count += 1
            # print(f"  - 发现重复行，将删除: {stripped_line[:90]}...")

    # 3. 将清理后的内容写回原文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(header_lines)
            f.writelines(unique_content_lines)
    except Exception as e:
        print(f"❌ 写回文件时出错 {file_path}: {e}")
        return

    # 4. 打印处理报告
    print(f"  - 头部行数: {len(header_lines)}")
    print(f"  - 原始内容行数: {original_content_count}")
    print(f"  - 删除的重复内容行数: {duplicate_count}")
    print(f"  - 清理后剩余独有行数: {len(seen_expressions)}")

def main():
    """
    主函数，遍历指定目录并清理所有 .txt 文件。
    """
    target_directory = os.path.join(DATA_PATH, "ready_to_test_alpha_list")
    
    print(f"🚀 开始扫描并清理目录中的 .txt 文件: {target_directory}\n")
    
    for filename in sorted(os.listdir(target_directory)): # 按文件名排序以获得一致的处理顺序
        if filename.endswith('.txt'):
            file_path = os.path.join(target_directory, filename)
            print(f"📄 正在处理文件: {filename}")
            clean_and_deduplicate_file(file_path)
            print("-" * 50)
            
    print("🎉 所有文件处理完毕。")

if __name__ == "__main__":
    main()


'''
📄 正在处理文件: test1_just_one_.txt
  - 头部行数: 9
  - 原始内容行数: 738
  - 删除的重复内容行数: 56
  - 清理后剩余独有行数: 682
--------------------------------------------------
📄 正在处理文件: test2_no_one.txt
  - 头部行数: 0
  - 原始内容行数: 296
  - 删除的重复内容行数: 0
  - 清理后剩余独有行数: 296
--------------------------------------------------
📄 正在处理文件: test3_just_one.txt
  - 头部行数: 7
  - 原始内容行数: 1074
  - 删除的重复内容行数: 353
  - 清理后剩余独有行数: 721
--------------------------------------------------
📄 正在处理文件: test4_claude_just_one.txt
  - 头部行数: 0
  - 原始内容行数: 1451
  - 删除的重复内容行数: 278
  - 清理后剩余独有行数: 1173
--------------------------------------------------
📄 正在处理文件: test5_notebooklm_just_one.txt
  - 头部行数: 9
  - 原始内容行数: 1915
  - 删除的重复内容行数: 430
  - 清理后剩余独有行数: 1485
--------------------------------------------------
📄 正在处理文件: test6_gpt.txt
  - 头部行数: 0
  - 原始内容行数: 1762
  - 删除的重复内容行数: 725
  - 清理后剩余独有行数: 1037
--------------------------------------------------
📄 正在处理文件: test7_gpt.txt
  - 头部行数: 0
  - 原始内容行数: 1000
  - 删除的重复内容行数: 0
  - 清理后剩余独有行数: 1000
--------------------------------------------------
📄 正在处理文件: unknow_alpha.txt
  - 头部行数: 0
  - 原始内容行数: 183
  - 删除的重复内容行数: 0
  - 清理后剩余独有行数: 183
--------------------------------------------------

'''