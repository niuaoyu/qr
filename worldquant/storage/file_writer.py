"""
文件写入模块 - 负责优质 Alpha 写入 TXT
"""
import os
import threading
from config import DEFAULT_RESULT_PATH

_write_lock = threading.Lock()


def write_quality_alpha(alpha_data, output_path=None):
    """
    将优质 Alpha（非 INFERIOR/UNKNOWN）写入文件

    Args:
        alpha_data: Alpha 数据字典
        output_path: 输出文件路径，默认使用配置路径

    Returns:
        bool: True 表示已写入，False 表示跳过
    """
    grade = (alpha_data.get('grade') or '').upper()

    # 只写入非 INFERIOR 和非 UNKNOWN 的结果
    if grade in ('INFERIOR', 'UNKNOWN', ''):
        return False

    # 获取统计数据
    is_data = alpha_data.get('is', {})

    content = f"""--------------------------------------------------
Alpha ID: {alpha_data.get('id')}, Author: {alpha_data.get('author', 'N/A')}
Expression: {alpha_data.get('expression', '')}
Sharpe: {is_data.get('sharpe')}
Turnover: {is_data.get('turnover')}
Fitness: {is_data.get('fitness')}
Grade: {grade}
--------------------------------------------------
"""

    path = output_path or DEFAULT_RESULT_PATH

    with _write_lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)

    return True


def prepend_to_file(filepath, content, lock=None):
    """
    线程安全的文件前置写入

    Args:
        filepath: 文件路径
        content: 要写入的内容
        lock: 线程锁（可选）
    """
    def _write():
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        old_content = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content + "\n" + old_content)

    if lock:
        with lock:
            _write()
    else:
        _write()
