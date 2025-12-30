"""
文件 input: config配置、JSON配置文件
文件 output: load_from_json() 生成payloads列表
文件 pos: JSON加载器，支持模板参数替换+settings组合
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import os
import re
import json
import itertools
from config import INPUT_DIR
from .expression_filter import filter_expressions


def load_from_json(json_file_path):
    """
    从JSON配置文件加载，生成payloads列表

    Args:
        json_file_path: JSON配置文件路径

    Returns:
        list: payloads列表
    """
    if not os.path.exists(json_file_path):
        print(f"❌ 配置文件不存在: {json_file_path}")
        return []

    with open(json_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    print("🧬 正在生成回测任务...")

    # 1. 生成所有表达式
    expressions = _generate_expressions(config)
    print(f"   - 生成 {len(expressions)} 个表达式")

    # 2. 过滤禁止的表达式
    expressions, _ = filter_expressions(expressions)
    print(f"   - 过滤后 {len(expressions)} 个表达式")

    # 3. 生成所有settings组合
    all_settings = _generate_settings(config)
    print(f"   - 生成 {len(all_settings)} 种设置组合")

    # 4. 笛卡尔积
    payloads = []
    for expr in expressions:
        for settings in all_settings:
            payloads.append({
                'type': 'REGULAR',
                'settings': settings.copy(),
                'regular': expr
            })

    print(f"✅ 生成 {len(payloads)} 个回测任务")
    return payloads


def _generate_expressions(config):
    """根据模板和参数生成所有表达式"""
    all_expressions = set()
    template_params = config.get('template_params', {})

    # 加载参数值（支持从文件读取）
    loaded_params = {k: _load_param_values(v) for k, v in template_params.items()}

    for template_item in config.get('alpha_templates', []):
        # 支持列表形式的模板（多行拼接）
        template = "".join(template_item) if isinstance(template_item, list) else template_item

        # 提取占位符
        placeholders = re.findall(r'\{(\w+)\}', template)
        param_values = [loaded_params.get(p, [f"{{{p}}}"]) for p in placeholders]

        # 笛卡尔积生成表达式
        for combo in itertools.product(*param_values):
            format_dict = dict(zip(placeholders, combo))
            all_expressions.add(template.format(**format_dict))

    return list(all_expressions)


def _load_param_values(value):
    """解析参数值（支持列表或TXT文件路径）"""
    if isinstance(value, list):
        return value

    if isinstance(value, str) and value.endswith('.txt'):
        file_path = os.path.join(INPUT_DIR, value)
        if not os.path.exists(file_path):
            file_path = value

        if os.path.exists(file_path):
            print(f"📖 从文件加载参数: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        else:
            print(f"⚠️ 参数文件未找到: {file_path}")
            return []

    return [value]


def _generate_settings(config):
    """生成所有settings组合"""
    settings_base = config.get('settings_base', {})
    settings_params = config.get('settings_params', {})

    if not settings_params:
        return [settings_base.copy()]

    varied_keys = list(settings_params.keys())
    varied_values = [settings_params[k] for k in varied_keys]

    all_settings = []
    for combo in itertools.product(*varied_values):
        new_settings = settings_base.copy()
        for i, key in enumerate(varied_keys):
            new_settings[key] = combo[i]
        all_settings.append(new_settings)

    return all_settings
