"""
WorldQuant Brain Alpha 回测系统 - 主入口
支持：多线程回测、数据库存储、优雅退出
"""
import os
import sys
import threading
from queue import Queue

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    SYSTEM_NAME, MAX_WORKERS, USER,
    DEFAULT_DB_PATH, DEFAULT_RESULT_PATH, INPUT_DIR, DEFAULT_SETTINGS,
    get_inferior_output_path, get_unknown_output_path
)
from core import sign_in, make_fingerprint, graceful, task_logger
from core.simulation import submit_simulation, poll_simulation_result, get_alpha_detail
from storage import init_db, save_alpha, check_exists, prepend_to_file, get_connection


# ============ 运行时配置 ============
USER_CHOICE = 'lab'  # 账户选择: lab, mylab, ubuntu, backup
INPUT_ALPHA_FILE = os.path.join(INPUT_DIR, 'ready_to_test_alpha_list','clean_alpha','test13_notebook.txt')
# INPUT_ALPHA_FILE = os.path.join(INPUT_DIR, 'ready_to_test_alpha_list','new_alphas_2000.txt')

# ============ 全局对象 ============
alpha_queue = Queue()
simulation_semaphore = threading.Semaphore(MAX_WORKERS)
result_file_lock = threading.Lock()

def load_alpha_expressions(filepath):
    """加载 Alpha 表达式列表"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def run_simulation_task(alpha_payload, config):
    """执行单个 Alpha 回测任务"""
    user_choice = config['user_choice']
    db_path = config['db_path']
    result_path = config['result_path']
    author_name = config['author_name']
    semaphore = config['semaphore']
    file_lock = config['file_lock']

    expression = alpha_payload.get('regular', '')
    settings = alpha_payload.get('settings', {})

    # 生成任务ID（用于计时）
    task_id = id(alpha_payload)

    # 1. 生成指纹并检查是否已存在
    fingerprint = make_fingerprint(expression, settings)
    conn = get_connection(db_path)

    if check_exists(conn, fingerprint):
        graceful.update_stats('skipped')
        task_logger.skip_task(expression, reason="数据库已存在")
        conn.close()
        return

    # 2. 登录并提交回测
    sess = sign_in(user_choice)
    if not sess:
        task_logger.log_error(task_id, "登录失败")
        conn.close()
        return

    # 开始任务计时
    task_logger.start_task(task_id, expression, settings)

    with semaphore:
        # 提交回测
        progress_url = submit_simulation(sess, alpha_payload)
        if not progress_url:
            sess = sign_in(user_choice)
            progress_url = submit_simulation(sess, alpha_payload)

        if not progress_url:
            graceful.update_stats('failed')
            task_logger.log_error(task_id, "提交失败")
            conn.close()
            return

        # 轮询结果
        alpha_id = poll_simulation_result(sess, progress_url)
        if not alpha_id:
            graceful.update_stats('failed')
            task_logger.log_error(task_id, "获取结果失败")
            conn.close()
            return

        # 获取详情
        alpha_detail = get_alpha_detail(sess, alpha_id)
        if not alpha_detail:
            task_logger.log_error(task_id, "获取详情失败")
            conn.close()
            return

        # 3. 保存到数据库
        alpha_detail['author'] = author_name
        is_data = alpha_detail.get('is', {})
        grade = alpha_detail.get('grade')

        if save_alpha(conn, alpha_detail, fingerprint):
            conn.commit()
            graceful.update_stats('success')
            task_logger.end_task(
                task_id,
                alpha_id=alpha_id,
                grade=grade,
                success=True,
                sharpe=is_data.get('sharpe'),
                fitness=is_data.get('fitness'),
                turnover=is_data.get('turnover')
            )

        # 4. 写入结果（根据 grade 分类写入不同文件）
        grade = alpha_detail.get('grade')
        is_data = alpha_detail.get('is', {})
        regular = alpha_detail.get('regular', {})
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
            # 写入 inferior 文件
            inferior_path = config.get('inferior_path')
            if inferior_path:
                prepend_to_file(inferior_path, content, file_lock)
        elif grade == 'UNKNOWN':
            # 写入 unknown 文件
            unknown_path = config.get('unknown_path')
            if unknown_path:
                prepend_to_file(unknown_path, content, file_lock)
        elif grade not in [None]:
            # 写入优质结果文件
            prepend_to_file(result_path, content, file_lock)

    conn.close()

def worker_loop(worker_id, config):
    """工作线程循环（支持优雅退出）"""
    print(f"🔧 Worker-{worker_id} 启动")
    while not graceful.is_shutdown():
        try:
            alpha_payload = alpha_queue.get(timeout=2)
            if alpha_payload is None:
                break
            run_simulation_task(alpha_payload, config)
            alpha_queue.task_done()
        except Exception:
            if alpha_queue.empty() or graceful.is_shutdown():
                break

    if graceful.is_shutdown():
        print(f"🔧 Worker-{worker_id} 收到退出信号")
    else:
        print(f"🔧 Worker-{worker_id} 完成")


def main():
    """主函数"""
    print(f"🚀 Alpha 回测系统启动 ({SYSTEM_NAME})")
    print(f"👤 账户: {USER_CHOICE}")
    print(f"📂 数据库: {DEFAULT_DB_PATH}")
    print(f"💡 按 Ctrl+C 可优雅退出")

    # 注册信号处理器
    graceful.register(alpha_queue)

    # 初始化数据库
    init_db(DEFAULT_DB_PATH)

    # 加载 Alpha 表达式
    if not os.path.exists(INPUT_ALPHA_FILE):
        print(f"❌ 输入文件不存在: {INPUT_ALPHA_FILE}")
        return

    alpha_expressions = load_alpha_expressions(INPUT_ALPHA_FILE)
    print(f"📥 已加载 {len(alpha_expressions)} 个表达式")

    # 设置总数
    graceful.set_total(len(alpha_expressions))

    # 准备工作线程配置
    author_name = USER[USER_CHOICE]['name'].split('@')[0]
    worker_config = {
        'user_choice': USER_CHOICE,
        'db_path': DEFAULT_DB_PATH,
        'result_path': DEFAULT_RESULT_PATH,
        'inferior_path': get_inferior_output_path(INPUT_ALPHA_FILE),
        'unknown_path': get_unknown_output_path(INPUT_ALPHA_FILE),
        'author_name': author_name,
        'semaphore': simulation_semaphore,
        'file_lock': result_file_lock
    }

    # 任务入队
    for expr in alpha_expressions:
        payload = {
            'type': 'REGULAR',
            'settings': DEFAULT_SETTINGS.copy(),
            'regular': expr
        }
        alpha_queue.put(payload)

    # 添加结束标记
    for _ in range(MAX_WORKERS):
        alpha_queue.put(None)

    # 启动工作线程
    threads = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i+1, worker_config), daemon=True)
        t.start()
        threads.append(t)

    # 等待线程完成（支持 Ctrl+C 中断）
    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        graceful.trigger_shutdown()
        # 等待线程响应退出信号
        for t in threads:
            t.join(timeout=3)

    # 打印最终统计
    graceful.print_stats()


if __name__ == "__main__":
    main()
