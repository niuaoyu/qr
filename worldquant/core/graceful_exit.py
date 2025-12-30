"""
优雅退出模块 - 支持 Ctrl+C 安全退出
"""
import sys
import threading


class GracefulExit:
    """优雅退出管理器"""

    def __init__(self):
        self.shutdown_flag = threading.Event()
        self.stats = {'total': 0, 'skipped': 0, 'success': 0, 'failed': 0}
        self.stats_lock = threading.Lock()
        self._queue = None

    def register(self, queue=None):
        """注册队列（用于清空）"""
        self._queue = queue

    def trigger_shutdown(self):
        """触发退出"""
        print("\n⚠️ 收到退出信号，等待当前任务完成...")
        self.shutdown_flag.set()

        # 清空队列，防止新任务被处理
        if self._queue:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except:
                    break

    def is_shutdown(self):
        """检查是否需要退出"""
        return self.shutdown_flag.is_set()

    def update_stats(self, key):
        """更新统计（线程安全）"""
        with self.stats_lock:
            self.stats[key] += 1

    def set_total(self, total):
        """设置总数"""
        self.stats['total'] = total

    def print_stats(self):
        """打印最终统计"""
        print(f"\n{'='*50}")
        print(f"📊 最终统计:")
        print(f"   总数: {self.stats['total']}")
        print(f"   成功: {self.stats['success']}")
        print(f"   跳过: {self.stats['skipped']}")
        print(f"   失败: {self.stats['failed']}")
        unprocessed = (self.stats['total'] - self.stats['success']
                       - self.stats['skipped'] - self.stats['failed'])
        print(f"   未处理: {unprocessed}")
        print(f"{'='*50}")

        if self.is_shutdown():
            print("⚠️ 程序被中断，部分任务未完成")
        else:
            print("✅ 所有任务完成")


# 全局实例
graceful = GracefulExit()
