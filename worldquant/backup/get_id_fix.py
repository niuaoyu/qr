import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 定义文件路径
# 使用 os.path.join 来构建路径，更具可移植性
# 注意：你的项目根目录是 c:\Users\nay\Desktop\qr\qr\worldquant
# file_path = r'c:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt'
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'idcode.txt'))
def get_id_fix():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 1. 读取文件的第一行
            first_line = f.readline()

            # 2. 使用 json.loads() 将该行字符串安全地解析成 Python 列表
            data_list = json.loads(first_line)

            # 3. 获取列表中的第一个元素（即邮箱地址）
            email = data_list[0]

            # 4. 使用 split('@') 方法分割邮箱，并取第一部分
            fix = email.split('@')[0]

            # 5. 打印最终结果
            # print(f"成功从文件 {file_path} 中提取！")
            # print(f"变量 'fix' 的值为: {fix}")
            return fix

    except FileNotFoundError:
        print(f"错误：文件未找到 at {file_path}")
    except json.JSONDecodeError:
        print(f"错误：文件内容 '{first_line.strip()}' 不是有效的JSON格式。")
    except IndexError:
        print("错误：文件中的列表为空，无法提取第一个元素。")
    except Exception as e:
        print(f"发生未知错误: {e}")
