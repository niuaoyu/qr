"""
文件写入模块 - 负责优质 Alpha 写入 TXT
"""
import os
import threading

# 输出文件路径
ALPHA_LIST_PATH = os.path.join(os.path.dirname(__file__), '..', 'io', 'result', 'alpha_list.txt')

_write_lock = threading.Lock()


def write_quality_alpha(alpha_data):
    """
    将优质 Alpha（非 INFERIOR/UNKNOWN）写入文件
    
    返回: True 表示已写入，False 表示跳过
    """
    grade = (alpha_data.get('grade') or '').upper()
    
    # 只写入非 INFERIOR 和非 UNKNOWN 的结果
    if grade in ('INFERIOR', 'UNKNOWN', ''):
        return False
    
    content = f"""--------------------------------------------------
Alpha ID: {alpha_data.get('id')}, Author: {alpha_data.get('author', 'N/A')}
Expression: {alpha_data.get('expression')}
Sharpe: {alpha_data.get('sharpe')}
Turnover: {alpha_data.get('turnover')}
Fitness: {alpha_data.get('fitness')}
Grade: {grade}
--------------------------------------------------
"""
    
    with _write_lock:
        # 确保目录存在
        os.makedirs(os.path.dirname(ALPHA_LIST_PATH), exist_ok=True)
        
        # 追加写入
        with open(ALPHA_LIST_PATH, 'a', encoding='utf-8') as f:
            f.write(content)
    
    return True
