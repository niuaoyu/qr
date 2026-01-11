"""
文件 input: config配置、core模块(auth/fingerprint/simulation)、storage模块
文件 output: run_backtest() 统一回测入口函数
文件 pos: 核心回测引擎，接收payloads列表执行多线程回测
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import threading
from queue import Queue

from config import (
    USER, DEFAULT_DB_PATH, DEFAULT_RESULT_PATH,
    get_inferior_output_path, get_unknown_output_path
)
from core import sign_in, make_fingerprint, graceful, task_logger
from core.simulation import submit_simulation, poll_simulation_result, get_alpha_detail
from storage import init_db, save_alpha, check_exists, prepend_to_file, get_connection


class BacktestEngine:
    """统一回测引擎"""

    def __init__(self, user_choice, input_file_path, max_workers=3):
        """
        初始化回测引擎

        Args:
            user_choice: 账户选择 (lab, mylab, ubuntu, backup)
            input_file_path: 输入文件路径（用于生成输出文件名）
            max_workers: 最大并发数
        """
        self.user_choice = user_choice
        self.input_file_path = input_file_path
        self.max_workers = max_workers

        # 路径配置
        self.db_path = DEFAULT_DB_PATH
        self.result_path = DEFAULT_RESULT_PATH
        self.inferior_path = get_inferior_output_path(input_file_path)
        self.unknown_path = get_unknown_output_path(input_file_path)

        # 作者名
        self.author_name = USER[user_choice]['name'].split('@')[0]

        # 线程同步对象
        self.alpha_queue = Queue()
        self.semaphore = threading.Semaphore(max_workers)
        self.file_lock = threading.Lock()

    def run(self, payloads):
        """
        执行回测

        Args:
            payloads: 回测任务列表，每个元素格式:
                {
                    'type': 'REGULAR',
                    'settings': {...},
                    'regular': '表达式'
                }
        """
        print(f"📥 共 {len(payloads)} 个回测任务")

        # 注册优雅退出
        graceful.register(self.alpha_queue)
        graceful.set_total(len(payloads))

        # 初始化数据库
        init_db(self.db_path)

        # 任务入队
        for payload in payloads:
            self.alpha_queue.put(payload)
        for _ in range(self.max_workers):
            self.alpha_queue.put(None)

        # 启动工作线程
        threads = []
        for i in range(self.max_workers):
            t = threading.Thread(
                target=self._worker_loop,
                args=(i + 1,),
                daemon=True
            )
            t.start()
            threads.append(t)

        # 等待完成（支持 Ctrl+C）
        try:
            while any(t.is_alive() for t in threads):
                for t in threads:
                    t.join(timeout=0.5)
        except KeyboardInterrupt:
            graceful.trigger_shutdown()
            for t in threads:
                t.join(timeout=3)

        # 打印统计
        graceful.print_stats()

    def _worker_loop(self, worker_id):
        """工作线程循环"""
        print(f"🔧 Worker-{worker_id} 启动")

        while not graceful.is_shutdown():
            try:
                payload = self.alpha_queue.get(timeout=2)
                if payload is None:
                    break
                self._run_task(payload)
                self.alpha_queue.task_done()
            except Exception:
                if self.alpha_queue.empty() or graceful.is_shutdown():
                    break

        if graceful.is_shutdown():
            print(f"🔧 Worker-{worker_id} 收到退出信号")
        else:
            print(f"🔧 Worker-{worker_id} 完成")

    def _run_task(self, payload):
        """执行单个回测任务"""
        expression = payload.get('regular', '')
        settings = payload.get('settings', {})
        task_id = id(payload)

        # 1. 指纹检查
        fingerprint = make_fingerprint(expression, settings)
        conn = get_connection(self.db_path)

        if check_exists(conn, fingerprint):
            graceful.update_stats('skipped')
            task_logger.skip_task(expression, reason="数据库已存在")
            conn.close()
            return

        # 2. 登录
        sess = sign_in(self.user_choice)
        if not sess:
            task_logger.log_error(task_id, "登录失败")
            conn.close()
            return

        # 开始计时
        task_logger.start_task(task_id, expression, settings)

        # 3. 提交回测（仅提交阶段需要控制并发）
        with self.semaphore:
            progress_url = submit_simulation(sess, payload)
            if not progress_url:
                sess = sign_in(self.user_choice)
                progress_url = submit_simulation(sess, payload)

        if not progress_url:
            graceful.update_stats('failed')
            task_logger.log_error(task_id, "提交失败")
            conn.close()
            return

        # 4. 轮询结果（轮询不占用 API 并发配额）
        alpha_id = poll_simulation_result(sess, progress_url)
        if not alpha_id:
            graceful.update_stats('failed')
            task_logger.log_error(task_id, "获取结果失败")
            conn.close()
            return

        # 5. 获取详情
        alpha_detail = get_alpha_detail(sess, alpha_id)
        if not alpha_detail:
            task_logger.log_error(task_id, "获取详情失败")
            conn.close()
            return

        # 6. 保存到数据库
        alpha_detail['author'] = self.author_name
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
                fitness=is_data.get('fitness')
            )

        # 7. 写入结果文件
        self._write_result(alpha_detail, alpha_id)

        conn.close()

    def _write_result(self, alpha_detail, alpha_id):
        """根据 grade 写入对应文件，非优质结果添加失败的 checks 信息"""
        grade = alpha_detail.get('grade')
        is_data = alpha_detail.get('is', {})
        regular = alpha_detail.get('regular', {})
        expr_code = regular.get('code', '') if isinstance(regular, dict) else ''

        content = (
            f"{'-'*50}\n"
            f"Alpha ID: {alpha_id}, Author: {self.author_name}\n"
            f"Expression: {expr_code}\n"
            f"Sharpe: {is_data.get('sharpe')}\n"
            f"Turnover: {is_data.get('turnover')}\n"
            f"Fitness: {is_data.get('fitness')}\n"
            f"Grade: {grade}\n"
        )

        # 对于非 INFERIOR/UNKNOWN 的结果，添加非 PASS 的 checks
        if grade not in ('INFERIOR', 'UNKNOWN', None, ''):
            checks = is_data.get('checks', [])
            failed_checks = [c for c in checks if c.get('result') != 'PASS']

            if failed_checks:
                content += "Checks:\n"
                for check in failed_checks:
                    name = check.get('name', 'UNKNOWN')
                    result = check.get('result', 'UNKNOWN')
                    value = check.get('value')
                    limit = check.get('limit')

                    # 格式化 check 信息
                    check_line = f"  - {name}: {result}"
                    if limit is not None and value is not None:
                        check_line += f" (limit: {limit}, value: {value})"
                    elif limit is not None:
                        check_line += f" (limit: {limit})"
                    elif value is not None:
                        check_line += f" (value: {value})"

                    content += check_line + "\n"

        content += f"{'-'*50}"

        if grade == 'INFERIOR':
            prepend_to_file(self.inferior_path, content, self.file_lock)
        elif grade == 'UNKNOWN':
            prepend_to_file(self.unknown_path, content, self.file_lock)
        elif grade not in [None]:
            prepend_to_file(self.result_path, content, self.file_lock)
