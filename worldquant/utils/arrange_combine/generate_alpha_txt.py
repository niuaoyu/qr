import sys
import os
import json
import re
import itertools
from datetime import datetime

# --- 路径设置 ---
# 将项目根目录添加到 sys.path，以便导入 main_part 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from qr.worldquant.global_config import DATA_PATH

def load_param_values(value):
    """
    解析参数值。如果是列表，直接返回。
    如果是以 .txt 结尾的字符串，则尝试从文件中读取行列表。
    """
    if isinstance(value, list):
        return value
    
    if isinstance(value, str) and value.endswith('.txt'):
        # 尝试拼接 DATA_PATH
        file_path = os.path.join(DATA_PATH, value)
        if not os.path.exists(file_path):
            # 如果拼接后不存在，尝试作为绝对路径
            file_path = value
        
        if os.path.exists(file_path):
            print(f"📖 从文件加载参数: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 读取非空行
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {e}")
                return []
        else:
            print(f"⚠️ 警告: 参数文件未找到: {file_path}")
            return []
            
    return [value]

def generate_simulation_payloads(config):
    """
    核心逻辑：读取配置，生成 Alpha 表达式组合。
    """
    print("🧬 正在生成排列组合...")

    # 1. 生成所有 Alpha 表达式 (Templates x Params)
    all_expressions = set()
    template_params_config = config.get('template_params', {})
    
    # 预先加载所有参数值（处理 txt 文件读取）
    loaded_params = {}
    for key, val in template_params_config.items():
        loaded_params[key] = load_param_values(val)

    for template_item in config['alpha_templates']:
        # 如果模板是列表（用于多行公式），则将其合并为单个字符串
        if isinstance(template_item, list):
            template = "".join(template_item)
        else:
            template = template_item

        # 找出模板中所有的占位符 {param}
        placeholders = re.findall(r'\{(\w+)\}', template)
        
        # 获取这些占位符对应的参数值列表
        # 如果配置中没定义某个参数，这就给一个包含该参数名的单元素列表，避免报错
        param_values_list = [loaded_params.get(p, [f"{{{p}}}"]) for p in placeholders]
        
        # 笛卡尔积：生成所有参数组合
        for combo in itertools.product(*param_values_list):
            format_dict = dict(zip(placeholders, combo))
            try:
                expression = template.format(**format_dict)
                all_expressions.add(expression)
            except Exception as e:
                print(f"⚠️ 格式化模板出错 '{template}': {e}")

    print(f"   - 生成了 {len(all_expressions)} 个唯一的 Alpha 表达式。")
    
    # 这里我们只需要表达式，不需要生成 Settings 组合，因为目的是生成 txt 列表
    return list(all_expressions)

def main():
    # 配置文件路径
    config_path = r"C:\Users\nay\Desktop\qr\qr\worldquant\arrange_combine\alpha_generator_config.json"
    # 输出目录
    output_dir = r"C:\Users\nay\Desktop\qr\qr\worldquant\ready_to_test_alpha_list"
    
    if not os.path.exists(config_path):
        print(f"❌ 找不到配置文件: {config_path}")
        return

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"📁 创建输出目录: {output_dir}")
        except Exception as e:
            print(f"❌ 无法创建输出目录: {e}")
            return

    print(f"📖 读取配置文件: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 生成表达式列表
    expressions = generate_simulation_payloads(config)
    
    if not expressions:
        print("⚠️ 未生成任何 Alpha 表达式。")
        return

    # 生成输出文件名 (带时间戳)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"generated_alphas_{timestamp}.txt")
    
    print(f"💾 正在写入文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for expr in sorted(expressions):
            f.write(expr + "\n")
    print(f"✅ 成功写入 {len(expressions)} 条 Alpha 表达式。")

if __name__ == "__main__":
    main()
