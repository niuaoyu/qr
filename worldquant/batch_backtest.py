"""
批量回测系统 - 基于配置文件生成 Alpha 组合并执行回测
支持：模板参数替换、设置参数组合、数据库存储、指纹去重、优雅退出
"""
import os
import sys
import json
import re
import itertools
import threading
from queue import Queue
from datetime import datetime

# 确保项目根目录在 Python 路径中
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import (
    SYSTEM_NAME, USER, DEFAULT_DB_PATH, DEFAULT_RESULT_PATH,
    INPUT_DIR, get_inferior_output_path, get_unknown_output_path
)
from core import sign_in, make_fingerprint
from core.simulation import submit_simulation, poll_simulation_result, get_alpha_detail
from core.task_logger import task_logger
from storage import init_db, save_alpha, check_exists, prepend_to_file, get_connection


# ============ 运行时配置 ============
USER_CHOICE = 'lab'
CONFIG_FILE = os.path.join(BASE_DIR, 'batch_config.json')
MAX_WORKERS = 3  # WorldQuant 平台支持最多 3 个并发

# ============ 全局对象 ============
alpha_queue = Queue()
simulation_semaphore = threading.Semaphore(MAX_WORKERS)
result_file_lock = threading.Lock()
stats = {'total': 0, 'skipped': 0, 'success': 0, 'failed': 0}
stats_lock = threading.Lock()

# ============ 优雅退出 ============
shutdown_flag = threading.Event()  # 退出标志
active_connections = []  # 活跃的数据库连接
connections_lock = threading.Lock()


def print_final_stats():
    """打印最终统计"""
    print(f"\n{'='*50}")
    print(f"📊 最终统计:")
    print(f"   总数: {stats['total']}")
    print(f"   成功: {stats['success']}")
    print(f"   跳过: {stats['skipped']}")
    print(f"   失败: {stats['failed']}")
    print(f"   未处理: {stats['total'] - stats['success'] - stats['skipped'] - stats['failed']}")
    print(f"{'='*50}")


def load_param_values(value):
    """
    解析参数值
    - 列表：直接返回
    - .txt 文件路径：从文件读取行列表
    """
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


def generate_payloads(config):
    """
    根据配置生成所有回测任务（表达式 × 设置的笛卡尔积）
    """
    print("🧬 正在生成回测任务...")

    # 1. 生成所有 Alpha 表达式
    all_expressions = set()
    template_params = config.get('template_params', {})
    loaded_params = {k: load_param_values(v) for k, v in template_params.items()}

    for template_item in config.get('alpha_templates', []):
        template = "".join(template_item) if isinstance(template_item, list) else template_item
        placeholders = re.findall(r'\{(\w+)\}', template)
        param_values = [loaded_params.get(p, [f"{{{p}}}"]) for p in placeholders]

        for combo in itertools.product(*param_values):
            format_dict = dict(zip(placeholders, combo))
            all_expressions.add(template.format(**format_dict))

    print(f"   - 生成 {len(all_expressions)} 个表达式")

    # 2. 生成所有 Settings 组合
    settings_base = config.get('settings_base', {})
    settings_params = config.get('settings_params', {})
    varied_keys = list(settings_params.keys())
    varied_values = [settings_params[k] for k in varied_keys]

    all_settings = []
    if varied_values:
        for combo in itertools.product(*varied_values):
            new_settings = settings_base.copy()
            for i, key in enumerate(varied_keys):
                new_settings[key] = combo[i]
            all_settings.append(new_settings)
    else:
        all_settings.append(settings_base.copy())

    print(f"   - 生成 {len(all_settings)} 种设置组合")

    # 3. 笛卡尔积
    payloads = []
    for expr in all_expressions:
        for settings in all_settings:
            payloads.append({
                'type': 'REGULAR',
                'settings': settings,
                'regular': expr
            })

    print(f"✅ 总任务数: {len(payloads)}")
    return payloads


def run_task(payload, config):
    """执行单个回测任务（复用 core 和 storage 模块）"""
    global stats
    user_choice = config['user_choice']
    db_path = config['db_path']
    result_path = config['result_path']
    author_name = config['author_name']

    expression = payload.get('regular', '')
    settings = payload.get('settings', {})

    # 生成任务ID（用于计时）
    task_id = id(payload)

    # 1. 指纹检查
    fingerprint = make_fingerprint(expression, settings)
    conn = get_connection(db_path)

    if check_exists(conn, fingerprint):
        with stats_lock:
            stats['skipped'] += 1
        task_logger.skip_task(expression, reason="数据库已存在")
        conn.close()
        return

    # 2. 登录
    sess = sign_in(user_choice)
    if not sess:
        task_logger.log_error(task_id, "登录失败")
        conn.close()
        return

    # 开始任务计时
    task_logger.start_task(task_id, expression, settings)

    # 3. 提交回测
    with simulation_semaphore:
        progress_url = submit_simulation(sess, payload)
        if not progress_url:
            sess = sign_in(user_choice)
            progress_url = submit_simulation(sess, payload)

        if not progress_url:
            with stats_lock:
                stats['failed'] += 1
            task_logger.log_error(task_id, "提交失败")
            conn.close()
            return

        # 4. 轮询结果
        alpha_id = poll_simulation_result(sess, progress_url)
        if not alpha_id:
            with stats_lock:
                stats['failed'] += 1
            task_logger.log_error(task_id, "获取结果失败")
            conn.close()
            return

        # 5. 获取详情
        detail = get_alpha_detail(sess, alpha_id)
        if not detail:
            task_logger.log_error(task_id, "获取详情失败")
            conn.close()
            return

        # 6. 保存到数据库
        detail['author'] = author_name
        is_data = detail.get('is', {})
        grade = detail.get('grade')

        if save_alpha(conn, detail, fingerprint):
            conn.commit()
            with stats_lock:
                stats['success'] += 1
            task_logger.end_task(
                task_id,
                alpha_id=alpha_id,
                grade=grade,
                success=True,
                sharpe=is_data.get('sharpe'),
                fitness=is_data.get('fitness')
            )

        # 7. 写入结果（根据 grade 分类写入不同文件）
        grade = detail.get('grade')
        is_data = detail.get('is', {})
        regular = detail.get('regular', {})
        expr_code = regular.get('code', '') if isinstance(regular, dict) else ''

        content = (
            f"{'-'*50}\n"
            f"Alpha ID: {alpha_id}, Author: {author_name}\n"
            f"Expression: {expr_code}\n"
            f"Sharpe: {is_data.get('sharpe')}\n"
            f"Turnover: {is_data.get('turnover')}\n"
            f"Fitness: {is_data.get('fitness')}\n"
            f"Grade: {grade}\n"
            f"{'-'*50}"
        )

        if grade == 'INFERIOR':
            inferior_path = config.get('inferior_path')
            if inferior_path:
                prepend_to_file(inferior_path, content, result_file_lock)
        elif grade == 'UNKNOWN':
            unknown_path = config.get('unknown_path')
            if unknown_path:
                prepend_to_file(unknown_path, content, result_file_lock)
        elif grade not in [None]:
            prepend_to_file(result_path, content, result_file_lock)

    conn.close()


def worker_loop(worker_id, config):
    """工作线程循环（支持优雅退出）"""
    print(f"🔧 Worker-{worker_id} 启动")
    while not shutdown_flag.is_set():
        try:
            payload = alpha_queue.get(timeout=2)
            if payload is None:
                break
            run_task(payload, config)
            alpha_queue.task_done()
        except Exception:
            if alpha_queue.empty() or shutdown_flag.is_set():
                break

    if shutdown_flag.is_set():
        print(f"🔧 Worker-{worker_id} 收到退出信号，已停止")
    else:
        print(f"🔧 Worker-{worker_id} 完成")


def main():
    """主函数"""
    global stats

    # 加载配置
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 配置文件不存在: {CONFIG_FILE}")
        print("请创建 batch_config.json 配置文件")
        return

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)

    user_choice = config.get('user_choice', USER_CHOICE)
    max_workers = config.get('max_workers', MAX_WORKERS)

    print(f"🚀 批量回测系统启动 ({SYSTEM_NAME})")
    print(f"👤 账户: {user_choice}")
    print(f"📂 数据库: {DEFAULT_DB_PATH}")
    print(f"💡 按 Ctrl+C 可优雅退出")

    # 初始化数据库（只执行一次，包含自动备份）
    init_db(DEFAULT_DB_PATH)

    # 生成任务
    payloads = generate_payloads(config)
    if not payloads:
        print("⚠️ 没有生成任何任务")
        return

    stats['total'] = len(payloads)

    # 准备工作配置
    author_name = USER[user_choice]['name'].split('@')[0]
    worker_config = {
        'user_choice': user_choice,
        'db_path': DEFAULT_DB_PATH,
        'result_path': DEFAULT_RESULT_PATH,
        'inferior_path': get_inferior_output_path(CONFIG_FILE),
        'unknown_path': get_unknown_output_path(CONFIG_FILE),
        'author_name': author_name
    }

    # 任务入队
    for p in payloads:
        alpha_queue.put(p)
    for _ in range(max_workers):
        alpha_queue.put(None)

    # 启动线程
    print(f"\n🔧 启动 {max_workers} 个工作线程...")
    threads = []
    for i in range(max_workers):
        t = threading.Thread(target=worker_loop, args=(i+1, worker_config), daemon=True)
        t.start()
        threads.append(t)

    # 等待线程完成（支持 Ctrl+C 中断）
    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        shutdown_flag.set()
        print("\n⚠️ 收到退出信号，等待当前任务完成...")
        # 清空队列
        while not alpha_queue.empty():
            try:
                alpha_queue.get_nowait()
            except:
                break
        # 等待线程响应
        for t in threads:
            t.join(timeout=3)

    # 打印最终统计
    print_final_stats()

    if shutdown_flag.is_set():
        print("⚠️ 程序被中断，部分任务未完成")
    else:
        print("✅ 所有任务完成")


if __name__ == "__main__":
    main()
