import sys
import os
import json
import time
import re
import itertools
import threading
from queue import Queue
from datetime import datetime

# --- 路径设置 ---
# 将项目根目录添加到 sys.path，以便导入 main_part 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main_part.global_config import DATA_PATH
from main_part.sign_in import sign_in

# --- 路径与用户配置 ---
# 配置文件路径
CONFIG_PATH = os.path.join(project_root, "arrange_combine", "alpha_generator_config.json")
# 结果输出目录
OUTPUT_DIR = os.path.join(project_root, "arrange_combine")
# 选择要使用的账户，可在 'lab', 'ubuntu', 'mylab' 中选择
USER_CHOICE = 'lab'

# --- 全局变量 ---
alpha_queue = Queue()
output_lock = threading.Lock()
simulation_semaphore = None

def load_param_values(value):
    """
    解析参数值。如果是列表，直接返回。
    如果是以 .txt 结尾的字符串，则尝试从文件中读取行列表。
    """
    if isinstance(value, list):
        return value
    
    if isinstance(value, str) and value.endswith('.txt'):
        file_path = os.path.join(DATA_PATH, value)
        if not os.path.exists(file_path):
            file_path = value
        
        if os.path.exists(file_path):
            print(f"📖 从文件加载参数: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {e}")
                return []
        else:
            print(f"⚠️ 警告: 参数文件未找到: {file_path}")
            return []
            
    return [value]

def generate_simulation_payloads(config):
    """
    核心逻辑：读取配置，生成 Alpha 表达式组合 和 Settings 组合的笛卡尔积。
    """
    print("🧬 正在生成所有回测任务...")

    # 1. 生成 Alpha 表达式
    all_expressions = set()
    template_params_config = config.get('template_params', {})
    loaded_params = {key: load_param_values(val) for key, val in template_params_config.items()}

    for template_item in config['alpha_templates']:
        template = "".join(template_item) if isinstance(template_item, list) else template_item
        placeholders = re.findall(r'\{(\w+)\}', template)
        param_values_list = [loaded_params.get(p, [f"{{{p}}}"]) for p in placeholders]
        
        for combo in itertools.product(*param_values_list):
            format_dict = dict(zip(placeholders, combo))
            all_expressions.add(template.format(**format_dict))

    print(f"   - 生成了 {len(all_expressions)} 个唯一的 Alpha 表达式。")

    # 2. 生成 Settings 组合
    settings_base = config['settings_base']
    settings_params_config = config.get('settings_params', {})
    varied_keys = list(settings_params_config.keys())
    varied_values_list = [settings_params_config[k] for k in varied_keys]
    
    all_settings_combos = []
    for combo in itertools.product(*varied_values_list):
        new_settings = settings_base.copy()
        for i, key in enumerate(varied_keys):
            new_settings[key] = combo[i]
        all_settings_combos.append(new_settings)

    print(f"   - 生成了 {len(all_settings_combos)} 种 Settings 配置。")

    # 3. 最终组合
    payloads = []
    for expr in all_expressions:
        for settings in all_settings_combos:
            payloads.append({'type': 'REGULAR', 'settings': settings, 'regular': expr})
    
    print(f"✅ 总共需要执行的回测任务数: {len(payloads)}")
    return payloads

def process_single_alpha(alpha_payload, user_choice, worker_id, output_file_path):
    """
    单个 Alpha 的回测、格式化并写入文件。
    """
    sess = sign_in(user_choice)
    if not sess:
        print(f"Worker-{worker_id} 登录失败，跳过任务。")
        return

    expression_code = alpha_payload.get('regular', 'N/A')
    settings_summary = {k: alpha_payload['settings'][k] for k in ['delay', 'neutralization', 'decay', 'universe'] if k in alpha_payload['settings']}
    print(f"▶️ Worker-{worker_id} 开始: {expression_code[:50]}... | {settings_summary}")

    result_data = None
    try:
        with simulation_semaphore:
            sim_resp = sess.post('https://api.worldquantbrain.com/simulations', json=alpha_payload)
            
            if sim_resp.status_code == 401:
                print(f"🔄 Worker-{worker_id} Token 过期，将自动在下一个任务中重新认证。")
                # 简单处理，让下一个任务重新登录
                return

            sim_progress_url = sim_resp.headers.get('Location')
            if not sim_progress_url:
                result_data = {'error': 'Submission Failed', 'details': sim_resp.text, 'grade': 'ERROR'}
            else:
                # 轮询等待结果
                alpha_id = None
                while True:
                    sim_progress_resp = sess.get(sim_progress_url)
                    if sim_progress_resp.status_code == 401:
                        print(f"🔄 Worker-{worker_id} Token 过期，将自动在下一个任务中重新认证。")
                        return
                    
                    retry_after = float(sim_progress_resp.headers.get('Retry-After', '0'))
                    if retry_after == 0:
                        sim_result = sim_progress_resp.json()
                        alpha_id = sim_result.get('alpha')
                        break
                    time.sleep(retry_after)
                
                if alpha_id:
                    alpha_detail_resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
                    result_data = alpha_detail_resp.json()
                    print(f"✅ Worker-{worker_id} 完成 Alpha ID: {alpha_id} | Grade: {result_data.get('grade')}")
                else:
                    result_data = {'error': 'Simulation Failed', 'details': sim_result, 'grade': 'FAIL'}

    except Exception as e:
        print(f"❌ Worker-{worker_id} 发生异常: {e}")
        result_data = {'error': 'Exception', 'details': str(e), 'grade': 'ERROR'}

    # --- 写入 TXT 文件 ---
    if result_data:
        settings_base_str = json.dumps({'settings_base': alpha_payload['settings']}, indent=4)
        
        alpha_id = result_data.get('id', 'N/A')
        grade = result_data.get('grade', 'N/A')
        is_stats = result_data.get('is', {}) or {}
        sharpe = is_stats.get('sharpe', 'N/A')
        turnover = is_stats.get('turnover', 'N/A')
        fitness = is_stats.get('fitness', 'N/A')

        sharpe_str = f"{sharpe:.4f}" if isinstance(sharpe, (int, float)) else str(sharpe)
        turnover_str = f"{turnover:.4f}" if isinstance(turnover, (int, float)) else str(turnover)
        fitness_str = f"{fitness:.4f}" if isinstance(fitness, (int, float)) else str(fitness)

        result_str = (
            f"Alpha ID: {alpha_id}\n"
            f"Expression: {expression_code}\n"
            f"Sharpe: {sharpe_str}\n"
            f"Turnover: {turnover_str}\n"
            f"Fitness: {fitness_str}\n"
            f"Grade: {grade}\n"
        )

        output_content = (
            f"{settings_base_str}\n\n"
            f"{result_str}"
            "--------------------------------------------------\n\n"
        )
        
        with output_lock:
            with open(output_file_path, 'a', encoding='utf-8') as f:
                f.write(output_content)

def worker_loop(user_choice, worker_id, output_file_path):
    while not alpha_queue.empty():
        try:
            payload = alpha_queue.get_nowait()
            process_single_alpha(payload, user_choice, worker_id, output_file_path)
            alpha_queue.task_done()
        except Queue.Empty:
            break
        except Exception as e:
            print(f"Worker-{worker_id} 致命错误: {e}")

def main():
    global simulation_semaphore
    start_time = datetime.now()
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    max_workers = config.get('max_workers', 3)
    simulation_semaphore = threading.Semaphore(max_workers)
    # user_choice = config.get('user_choice', 'lab') # 使用顶部的 USER_CHOICE 设置

    output_file_path = os.path.join(OUTPUT_DIR, f"backtest_results_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
    
    payloads = generate_simulation_payloads(config)
    if not payloads:
        print("⚠️ 没有生成任何任务，请检查配置。")
        return

    for p in payloads:
        alpha_queue.put(p)

    print(f"\n🚀 启动 {max_workers} 个工作线程开始回测... 结果将写入: {output_file_path}")
    threads = []
    for i in range(max_workers):
        t = threading.Thread(target=worker_loop, args=(USER_CHOICE, i+1, output_file_path))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(f"\n🎉 所有回测任务完成！报告已保存至 {output_file_path}")

if __name__ == "__main__":
    main()
