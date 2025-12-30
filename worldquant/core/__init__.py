"""
核心模块 - 认证、回测、指纹生成、优雅退出、任务日志、回测引擎
"""
from .auth import sign_in
from .fingerprint import make_fingerprint
from .simulation import submit_simulation, poll_simulation_result, get_alpha_detail
from .graceful_exit import graceful, GracefulExit
from .task_logger import task_logger, TaskLogger
from .backtest_engine import BacktestEngine

__all__ = [
    'sign_in',
    'make_fingerprint',
    'submit_simulation',
    'poll_simulation_result',
    'get_alpha_detail',
    'graceful',
    'GracefulExit',
    'task_logger',
    'TaskLogger',
    'BacktestEngine'
]
