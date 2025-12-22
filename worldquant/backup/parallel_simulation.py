import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import concurrent.futures
import json
import time
from datetime import datetime

# 确保其他模块可以被正确导入


# 从您现有的脚本中导入必要的组件
from main_part.sign_in import sign_in
from qr.worldquant.main_part.load_alpha_expressions import load_alpha_expressions
from qr.worldquant.backup.write_txt import write_lines

# --- 结果保存函数 (逻辑源自您的 send.py) ---


import threading
from queue import Queue

# 用于线程安全地从文件读取下一个alpha
alpha_queue = Queue()
file_lock = threading.Lock()
# 全局信号量，控制同时运行的回测数量
simulation_semaphore = threading.Semaphore(3)
# 全局计数器，用于统计 grade != 'INFERIOR' 的数量
submit_count = 0
submit_count_lock = threading.Lock()


def save_alpha_result(result_entry, start_timestamp,worker_id):
    """每个worker保存到独立的文件"""
    result_dir = r"C:\Users\nay\Desktop\qr\qr\worldquant\result"
    os.makedirs(result_dir, exist_ok=True)
    filename = f"{start_timestamp}_worker{worker_id}_results.txt"
    filepath = os.path.join(result_dir, filename)
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(result_entry + "\n")
    print(f"📝 Worker-{worker_id} 结果已追加至: {filepath}")


# --- “工人”函数：处理单个Alpha回测的完整流程 ---
def process_single_alpha(alpha_payload, start_timestamp, worker_id):
    """
    处理单个alpha的回测，包含登录、提交、轮询、4小时超时重连和保存结果的完整逻辑。
    这个函数是线程安全的，因为它为每个线程创建了独立的 session。
    增加 worker_id 参数，用于区分不同worker的结果文件
    """
    # 每个线程都应该有自己的 session，避免冲突
    sess = sign_in()
    if not sess:
        print(f"工作线程登录失败，Alpha: {alpha_payload.get('regular')}")
        return

    expression_code = alpha_payload.get('regular', 'N/A')
    print(f"▶️ 开始处理 Alpha: {expression_code}")

    # 包含重试逻辑的无限循环，直到当前alpha成功或彻底失败
    while True:
        try:
            # 获取信号量（如果已有3个在运行，这里会阻塞等待）
            with simulation_semaphore:
                print(f"▶️ Worker-{worker_id} 开始处理: {expression_code}")
                # 1. 提交模拟任务
                sim_resp = sess.post(
                    'https://api.worldquantbrain.com/simulations',
                    json=alpha_payload
                )
                if sim_resp.status_code == 401:
                    print(f"Token 过期，正在为 Alpha '{expression_code}' 重新认证...")
                    sess = sign_in()
                    continue # 重新尝试提交

                sim_progress_url = sim_resp.headers.get('Location')
                if not sim_progress_url:
                    print(f"提交失败: {sim_resp.text}")
                    result_entry = (
                        f"Expression: {expression_code}\n"
                        f"Status: SUBMISSION_FAILED\n"
                        f"Reason: {sim_resp.text}\n"
                        f"{'-'*50}"
                    )
                    save_alpha_result(result_entry, start_timestamp, worker_id)
                    return # 结束这个alpha的处理

                # 2. 轮询模拟进度
                alpha_id = None
                while True:
                    sim_progress_resp = sess.get(sim_progress_url)
                    if sim_progress_resp.status_code == 401:
                        print(f"轮询时 Token 过期，正在为 Alpha '{expression_code}' 重新认证...")
                        sess = sign_in()
                        continue
                    
                    retry_after_sec = float(sim_progress_resp.headers.get('Retry-After', '0'))
                    if retry_after_sec == 0:
                        sim_result = sim_progress_resp.json()
                        if 'alpha' not in sim_result:
                            print(f"模拟失败，响应: {sim_result}")
                            result_entry = (
                                f"Expression: {expression_code}\n"
                                f"Status: SIMULATION_FAILED\n"
                                f"Reason: {json.dumps(sim_result)}\n"
                                f"{'-'*50}"
                            )
                            save_alpha_result(result_entry, start_timestamp, worker_id)
                            return # 结束这个alpha的处理
                        alpha_id = sim_result['alpha']
                        break
                    time.sleep(retry_after_sec)
                
                if not alpha_id:
                    print(f"未能获取 Alpha ID，任务终止: {expression_code}")
                    return

                print(f'✅ 获取到 Alpha ID: {alpha_id} (来自: {expression_code})')

                # 3. 获取 Alpha 详细结果
                alpha_detail_resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
                if alpha_detail_resp.status_code == 401:
                    print(f"获取详情时 Token 过期，正在为 Alpha ID '{alpha_id}' 重新认证...")
                    sess = sign_in()
                    continue # 重试获取详情
                
                alpha_detail = alpha_detail_resp.json()
                grade = alpha_detail.get('grade')
                print(f"Alpha Status: {grade} for ID: {alpha_id}")

                # 4. 提取并立即保存结果
                stats = alpha_detail.get('is', {})
                sharpe = stats.get('sharpe')
                turnover = stats.get('turnover')
                fitness = stats.get('fitness')
                
                result_entry = (
                    f"Alpha ID: {alpha_id}\n"
                    f"Expression: {expression_code}\n"
                    f"Sharpe: {sharpe}\n"
                    f"Turnover: {turnover}\n"
                    f"Fitness: {fitness}\n"
                    f"Grade: {grade}\n"
                    f"{'-'*50}"
                )
                save_alpha_result(result_entry, start_timestamp, worker_id)
                
                # 如果alpha表现好，额外记录
                if grade != 'INFERIOR':
                    with submit_count_lock:
                        global submit_count
                        submit_count += 1
                    write_lines(r"C:\Users\nay\Desktop\qr\qr\worldquant\utils\logtxt\alphalist.txt", alpha_id)

                break # 成功完成，退出当前alpha的重试循环

        except Exception as e:
            print(f'处理 Alpha {expression_code} 时发生未知错误: {e}')
            time.sleep(10)
            try:
                print("尝试在异常后重新登录...")
                sess = sign_in()
            except Exception as sign_in_e:
                print(f"异常后重新登录失败: {sign_in_e}")
                time.sleep(30) # 等待更长时间
            # 外层循环将继续，重试当前alpha



def worker_loop(worker_id, start_timestamp):
    """每个worker的主循环，不断从队列获取任务"""
    while True:
        try:
            alpha_payload = alpha_queue.get(timeout=5)  # 5秒超时
            if alpha_payload is None:  # 毒丸信号，退出
                break
            process_single_alpha(alpha_payload, start_timestamp, worker_id)
            alpha_queue.task_done()
        except:
            # 队列空了，检查是否还有任务
            if alpha_queue.empty():
                break


# --- 主函数：负责调度 ---
def main():
    # 设置并行任务（工人）数量，根据您的配额设置为3
    MAX_WORKERS = 3
    
    input_file_path = r'C:\Users\nay\Desktop\qr\qr\worldquant\ready_to_test_alpha_list\test5_notebooklm.txt'
    print("正在加载 Alpha 表达式...")
    alpha_expressions = load_alpha_expressions(input_file_path)
    
    # 准备回测请求体列表
    alpha_list = []
    for alpha_expression in alpha_expressions:
        simulation_data = {
            'type': 'REGULAR',
            'settings': {
                'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000',
                'delay': 1, 'decay': 0, 'neutralization': 'SUBINDUSTRY',
                'truncation': 0.01, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
                'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            },
            'regular': alpha_expression
        }
        alpha_queue.put(simulation_data)
            # 添加毒丸信号
    for _ in range(MAX_WORKERS):
        alpha_queue.put(None)
    
    start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 启动3个worker线程
    threads = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i+1, start_timestamp))
        t.start()
        threads.append(t)
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print("所有 Alpha 回测任务已处理完毕。")

    # 重命名文件，加上 submit_count
    if os.path.exists(input_file_path):
        dir_name = os.path.dirname(input_file_path)
        base_name = os.path.basename(input_file_path)
        name, ext = os.path.splitext(base_name)
        new_name = f"{name}_{submit_count}{ext}"
        new_path = os.path.join(dir_name, new_name)
        try:
            os.rename(input_file_path, new_path)
            print(f"📄 文件已重命名为: {new_path}")
        except Exception as e:
            print(f"❌ 重命名文件失败: {e}")

if __name__ == "__main__":
    main()