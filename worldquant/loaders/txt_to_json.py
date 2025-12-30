"""
文件 input: TXT表达式文件路径
文件 output: txt_to_json_templates() 转换函数
文件 pos: 工具模块，将TXT表达式转换为JSON alpha_templates格式
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import os
import json


def txt_to_json_templates(txt_file_path, output_json_path=None):
    """
    将TXT表达式文件转换为JSON配置文件的alpha_templates格式

    Args:
        txt_file_path: TXT文件路径（每行一个表达式）
        output_json_path: 输出JSON路径（可选，不填则只返回不写文件）

    Returns:
        list: alpha_templates 列表
    """
    if not os.path.exists(txt_file_path):
        print(f"❌ 文件不存在: {txt_file_path}")
        return []

    # 读取表达式
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        expressions = [line.strip() for line in f if line.strip()]

    print(f"📖 读取 {len(expressions)} 个表达式")

    # 如果指定了输出路径，写入JSON
    if output_json_path:
        _write_to_json(expressions, output_json_path)

    return expressions


def _write_to_json(expressions, output_path):
    """将表达式写入JSON配置文件"""
    # 如果文件存在，读取并更新；否则创建新的
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['alpha_templates'] = expressions
        print(f"📝 更新已有配置: {output_path}")
    else:
        config = {
            "alpha_templates": expressions,
            "template_params": {},
            "settings_base": {},
            "settings_params": {}
        }
        print(f"📝 创建新配置: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"✅ 已写入 {len(expressions)} 个表达式到 alpha_templates")
