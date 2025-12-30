"""
任务日志模块 - 支持完整表达式显示和实时计时
"""
import sys
import time
import threading
from datetime import datetime


class TaskLogger:
    """任务日志记录器 - 支持实时计时显示"""

    def __init__(self):
        self._lock = threading.Lock()
        self._task_data = {}  # task_id -> {'start_time', 'timer_stop', 'timer'}
        self._active_timer_task = None  # 当前显示计时的任务

    def start_task(self, task_id, expression, settings=None):
        """
        开始任务，启动实时计时器

        参数:
            task_id: 任务唯一标识
            expression: 完整的 Alpha 表达式
            settings: 可选的设置信息字典
        """
        start_time = time.time()

        with self._lock:
            # 如果有其他任务正在显示计时，先清除
            self._clear_timer_line()

            # 打印开始信息
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n{'─'*70}")
            print(f"▶️ [{current_time}] 开始任务")
            print(f"   表达式: {expression}")
            if settings:
                key_settings = {k: v for k, v in settings.items()
                               if k in ['neutralization', 'delay', 'decay', 'universe']}
                if key_settings:
                    print(f"   设置: {key_settings}")

        # 停止之前的计时器（如果有）
        if task_id in self._task_data:
            self._task_data[task_id]['timer_stop'].set()

        # 启动新的计时器
        timer_stop = threading.Event()
        timer = threading.Thread(
            target=self._timer_loop,
            args=(task_id, start_time, timer_stop),
            daemon=True
        )

        self._task_data[task_id] = {
            'start_time': start_time,
            'timer_stop': timer_stop,
            'timer': timer
        }

        self._active_timer_task = task_id
        timer.start()

    def _timer_loop(self, task_id, start_time, stop_event):
        """计时器循环 - 每秒更新一次"""
        while not stop_event.is_set():
            elapsed = int(time.time() - start_time)
            with self._lock:
                if self._active_timer_task == task_id:
                    # 使用 \r 覆盖当前行显示实时计时
                    sys.stdout.write(f"\r   ⏱️ 运行中... {elapsed}秒")
                    sys.stdout.flush()
            stop_event.wait(1)  # 等待1秒或被停止

    def _clear_timer_line(self):
        """清除计时行（需要在锁内调用）"""
        if self._active_timer_task:
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()

    def _stop_task_timer(self, task_id):
        """停止任务计时器，返回用时"""
        task_data = self._task_data.pop(task_id, None)

        if task_data:
            task_data['timer_stop'].set()
            task_data['timer'].join(timeout=0.5)
            elapsed = time.time() - task_data['start_time']
            return elapsed
        return 0

    def end_task(self, task_id, alpha_id=None, grade=None, success=True,
                 sharpe=None, fitness=None):
        """
        结束任务，停止计时器，打印结果

        参数:
            task_id: 任务唯一标识
            alpha_id: Alpha ID
            grade: 评级
            success: 是否成功
            sharpe: Sharpe 值
            fitness: Fitness 值
        """
        # 停止计时器
        elapsed = self._stop_task_timer(task_id)
        elapsed_str = self._format_duration(elapsed)

        with self._lock:
            # 清除计时行
            if self._active_timer_task == task_id:
                self._clear_timer_line()
                self._active_timer_task = None

            # 打印最终结果
            if success:
                metrics = []
                if sharpe is not None:
                    metrics.append(f"Sharpe={sharpe:.2f}")
                if fitness is not None:
                    metrics.append(f"Fitness={fitness:.2f}")
                metrics_str = f" | {', '.join(metrics)}" if metrics else ""
                print(f"✅ 完成 | ID: {alpha_id} | Grade: {grade}{metrics_str} | ⏱️ {elapsed_str}")
            else:
                print(f"❌ 失败 | ⏱️ {elapsed_str}")

    def skip_task(self, expression, reason="已存在"):
        """
        跳过任务

        参数:
            expression: 完整的 Alpha 表达式
            reason: 跳过原因
        """
        with self._lock:
            self._clear_timer_line()
            print(f"\n⏭️ 跳过 ({reason})")
            print(f"   表达式: {expression}")

    def log_error(self, task_id, error_msg):
        """
        记录错误

        参数:
            task_id: 任务唯一标识
            error_msg: 错误信息
        """
        # 停止计时器
        elapsed = self._stop_task_timer(task_id)
        elapsed_str = self._format_duration(elapsed) if elapsed > 0 else "0秒"

        with self._lock:
            if self._active_timer_task == task_id:
                self._clear_timer_line()
                self._active_timer_task = None
            print(f"❌ 错误 | {error_msg} | ⏱️ {elapsed_str}")

    def _format_duration(self, seconds):
        """格式化时长显示"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.0f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}时{minutes}分"


# 全局实例
task_logger = TaskLogger()
