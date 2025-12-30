"""
文件 input: 表达式字符串
文件 output: is_forbidden() 检查函数, filter_expressions() 过滤函数
文件 pos: 表达式过滤模块，管理禁止规则
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import re


# ============ 禁止规则 ============
FORBIDDEN_PATTERNS = [
    # 规则1: group_neutralize 包含 ts_backfill 除法
    (r'group_neutralize\s*\([^)]*ts_backfill[^)]*\/[^)]*ts_backfill',
     'group_neutralize(...ts_backfill.../ts_backfill...)'),

    # 规则2: -rank(ts_corr(...))
    (r'^-rank\s*\(\s*ts_corr\s*\(',
     '-rank(ts_corr(...))'),

    # 规则3: ts_rank(ts_backfill(...) / ..., ...)
    (r'ts_rank\s*\(\s*ts_backfill\s*\([^)]+\)\s*\/',
     'ts_rank(ts_backfill(...) / ...)'),
]


def is_forbidden(expression):
    """
    检查表达式是否匹配禁止规则

    Returns:
        tuple: (是否禁止, 规则名称)
    """
    for pattern, name in FORBIDDEN_PATTERNS:
        if re.search(pattern, expression, re.IGNORECASE):
            return True, name
    return False, None


def filter_expressions(expressions):
    """
    过滤表达式列表，移除禁止的模式

    Args:
        expressions: 表达式列表

    Returns:
        tuple: (保留的表达式列表, 被过滤的数量)
    """
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
