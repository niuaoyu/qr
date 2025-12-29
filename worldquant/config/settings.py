"""
全局配置模块
"""
import os
import platform
import threading
from queue import Queue

# 系统信息
SYSTEM_NAME = platform.system()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 并发配置
MAX_WORKERS = 3
alpha_queue = Queue()
simulation_semaphore = threading.Semaphore(3)
result_write_lock = threading.Lock()

# 用户账户
USER = {
    'lab': {"name": "niuaoyula@163.com", "password": "NAYnay232408."},
    'mylab': {"name": "672019598@qq.com", "password": "NAYnay232408."},
    'ubuntu': {"name": "2734849800@qq.com", "password": "NAYnay232408."},
    'backup': {"name": "littlespark7602@gmail.com", "password": "NAYnay232408."}
}

# 默认回测设置
DEFAULT_SETTINGS = {
    'instrumentType': 'EQUITY',
    'region': 'USA',
    'universe': 'TOP3000',
    'delay': 1,
    'decay': 0,
    'neutralization': 'SUBINDUSTRY',
    'truncation': 0.01,
    'pasteurization': 'ON',
    'nanHandling': 'ON',
    'unitHandling': 'VERIFY'
}
