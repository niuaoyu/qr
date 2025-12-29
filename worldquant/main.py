import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from global_config import DATA_PATH, BASE_DIR, system_name, USER
from data.load_alpha_expressions import load_alpha_expressions
from data.sqlite.db_utils import init_db
from sim_engine import run_simulation_task
import threading
from queue import Queue

# --- Configuration ---
USER_CHOICE = 'lab'  # ubuntu, lab, mylab
MAX_WORKERS = 3
INPUT_ALPHA_FILE = os.path.join(BASE_DIR, "data", "ready_to_test_alpha_list", "new_alphas_2000.txt")
# Paths
# Using BASE_DIR to ensure we point to worldquant directory structure correctly
DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "alphas.db")
TXT_RESULT_PATH = os.path.join(BASE_DIR, "data", "result", "alpha_list.txt")

# Global Objects
alpha_queue = Queue()
simulation_semaphore = threading.Semaphore(MAX_WORKERS)
result_file_lock = threading.Lock()

def worker_loop(worker_id, config):
    """Worker thread loop."""
    print(f"🔧 Worker-{worker_id} started.")
    while True:
        try:
            alpha_payload = alpha_queue.get(timeout=5)
            if alpha_payload is None:
                break
            
            run_simulation_task(alpha_payload, config)
            
            alpha_queue.task_done()
        except Exception:
            if alpha_queue.empty():
                break
    print(f"🔧 Worker-{worker_id} finished.")

# --- 主函数：负责调度 ---
def main():
    print(f"🚀 Starting Alpha Backtest System ({system_name})")
    print(f"👤 User: {USER_CHOICE}")
    print(f"📂 DB Path: {DB_PATH}")
    
    # Initialize DB
    init_db(DB_PATH)
    
    # Load Alphas
    if not os.path.exists(INPUT_ALPHA_FILE):
        print(f"❌ Input file not found: {INPUT_ALPHA_FILE}")
        return
        
    alpha_expressions = load_alpha_expressions(INPUT_ALPHA_FILE)
    print(f"📥 Loaded {len(alpha_expressions)} expressions.")
    
    # Prepare Config for Workers
    author_name = USER[USER_CHOICE]['name'].split('@')[0]
    worker_config = {
        'user_choice': USER_CHOICE,
        'db_path': DB_PATH,
        'txt_result_path': TXT_RESULT_PATH,
        'author_name': author_name,
        'semaphore': simulation_semaphore,
        'file_lock': result_file_lock
    }
    
    # Enqueue Tasks
    for expr in alpha_expressions:
        payload = {
            'type': 'REGULAR',
            'settings': {
                'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000',
                'delay': 1, 'decay': 0, 'neutralization': 'SUBINDUSTRY',
                'truncation': 0.01, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
                'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            },
            'regular': expr
        }
        alpha_queue.put(payload)
    
    # Add Poison Pills
    for _ in range(MAX_WORKERS):
        alpha_queue.put(None)
    
    # Start Threads
    threads = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i+1, worker_config))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print("✅ All tasks completed.")

if __name__ == "__main__":
    main()


#     前置要求1.需要在三台电脑（Windows Linux环境）同时可以运行该代码，故路径不可写死，都放在代码的最上面，要按照这个对读写路径的写法SAVE_RESULT_DIR = os.path.join(DATA_PATH, "result","version2") 2. 同时因为需要有三个账号，在三台电脑运行，需要设USER_CHOICE = 'lab' # 选择哪个账户？ubuntu、lab、mylab来确定是那个环境，这需要读取from main_part.sign_in import sign_in自己写的sign_in方法
# 任何需要修改的配置信息，都不允许卸载函数里面，写在每个函数顶上，

# 问题：C:\qr\qr\worldquant\main.py这个函数实现逻辑是登录后，读取待测试的a表达式的txt，然后同步三个提交测试，存下来结果写入到txt文件里，现在需要改成，
# 1.读取txt表达式后，按照数据库里的每行的设置结构，形成当前表达式的唯一id，检测二者是否一样，如果一样，就不再进行回测，回测的结果存到数据库里，对于结果不是inferior和unknown的多加一步操作，写入到C:\qr\qr\worldquant\data\result\alpha_list.txt这个文件里，按照--------------------------------------------------
#  Alpha ID: npb6Zj9x
# Expression: rank(fnd6_newqv1300_lcoq / assets)
# Sharpe: 1.79
# Turnover: 0.0316
# Fitness: 1.27
# Grade: AVERAGE
# --------------------------------------------------这个格式，在  Alpha ID: npb6Zj9x这里写成 Alpha ID: npb6Zj9x，author：LHxxxx，写代码的时候，把可以复用的代码别写在一起，避免一个脚本行数过多，

# 先别写，理解代码再说
