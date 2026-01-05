"""
TXT 表达式转 JSON 配置工具
用法: python convert_txt.py <txt文件路径> [json输出路径]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loaders import txt_to_json_templates

# python convert_txt.py C:\qr\qr\worldquant\io\input\ready_to_test_alpha_list\clean_alpha\temp_test.txt C:\qr\qr\worldquant\batch_config.json
def main():
    if len(sys.argv) < 2:
        print("用法: python convert_txt.py <txt文件路径> [json输出路径]")
        print("示例: python convert_txt.py io/input/alphas.txt batch_config.json")
        return

    txt_path = sys.argv[1]
    json_path = sys.argv[2] if len(sys.argv) > 2 else 'batch_config.json'

    txt_to_json_templates(txt_path, json_path)
    print(f"\n✅ 转换完成，现在可以运行: python main.py")


if __name__ == "__main__":
    main()
