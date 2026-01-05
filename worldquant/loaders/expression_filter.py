"""
文件 input: filter_rules.json 规则配置
文件 output: is_forbidden() 检查函数, filter_expressions() 过滤函数
文件 pos: 表达式过滤模块，从JSON读取规则
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import re
import os
import json


# 加载规则配置
def _load_rules():
    """从JSON文件加载过滤规则"""
    rules_path = os.path.join(os.path.dirname(__file__), 'filter_rules.json')

    if not os.path.exists(rules_path):
        print(f"⚠️ 规则文件不存在: {rules_path}")
        return []

    with open(rules_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    patterns = []
    for rule in config.get('forbidden_templates', []):
        patterns.append((rule['regex'], rule['description']))

    return patterns


# 加载规则
FORBIDDEN_PATTERNS = _load_rules()


def reload_rules():
    """重新加载规则（规则文件修改后调用）"""
    global FORBIDDEN_PATTERNS
    FORBIDDEN_PATTERNS = _load_rules()
    print(f"✅ 已加载 {len(FORBIDDEN_PATTERNS)} 条过滤规则")


def is_forbidden(expression):
    """检查表达式是否匹配禁止规则"""
    for pattern, name in FORBIDDEN_PATTERNS:
        if re.search(pattern, expression, re.IGNORECASE):
            return True, name
    return False, None


def filter_expressions(expressions):
    """过滤表达式列表，移除禁止的模式"""
    kept = []
    removed_count = 0

    for expr in expressions:
        forbidden, rule_name = is_forbidden(expr)
        if forbidden:
            removed_count += 1
        else:
            kept.append(expr)

    if removed_count > 0:
        print(f"⚠️ 过滤了 {removed_count} 个禁止模式的表达式")

    return kept, removed_count
