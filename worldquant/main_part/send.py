### 将α一个个发挥服务器回测，并检查是否断线，如果断线则重连


import logging
import os
from datetime import datetime
logging.basicConfig(filename='simulation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# from utils.allSubmitOrNot import get_alpha_checks
from utils.writeTxt import write_lines

from time import sleep

from main_part.sign_in import sign_in
sess = sign_in()

def send_alpha_list(sess, alpha_list):
    submit_count = 0
    next_start_index = 0

    results_for_file = []
    
    # 确保结果文件夹存在
    result_dir = r"C:\Users\nay\Desktop\qr\qr\worldquant\result"
    os.makedirs(result_dir, exist_ok=True)

    for alpha in alpha_list:
            next_start_index += 1
            while True:
                try:
                    sim_resp = sess.post(
                        'https://api.worldquantbrain.com/simulations',
                        json=alpha
                    )
                    if sim_resp.status_code == 401:
                        print("Token expired, re-authenticating...")
                        sess = sign_in()
                        continue

                    sim_progress_url = sim_resp.headers.get('Location')
                    if not sim_progress_url:
                        print(f"Submission failed: {sim_resp.text}")
                        break

                    while True:
                        sim_progress_resp = sess.get(sim_progress_url)
                        if sim_progress_resp.status_code == 401:
                            print("Token expired during polling, re-authenticating...")
                            sess = sign_in()
                            continue
                        retry_after_sec = float(sim_progress_resp.headers.get('Retry-After', '0'))
                        if retry_after_sec == 0:
                            break
                        sleep(retry_after_sec)
                    alpha_id = sim_progress_resp.json()['alpha']
                    print(f'Alpha ID: {alpha_id}')

                    # 获取 Alpha 的详细结果状态
                    alpha_detail_resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
                    if alpha_detail_resp.status_code == 401:
                        print("Token expired getting details, re-authenticating...")
                        sess = sign_in()
                        continue
                    alpha_detail = alpha_detail_resp.json()
                    print(f"Alpha Status: {alpha_detail.get('grade')}")

                    # 提取所需信息并准备写入文件
                    stats = alpha_detail.get('is', {})
                    sharpe = stats.get('sharpe')
                    turnover = stats.get('turnover')
                    fitness = stats.get('fitness')
                    expression = alpha_detail.get('regular', {}).get('code')
                    
                    result_entry = (
                        f"Alpha ID: {alpha_id}\n"
                        f"Expression: {expression}\n"
                        f"Sharpe: {sharpe}\n"
                        f"Turnover: {turnover}\n"
                        f"Fitness: {fitness}\n"
                        f"{'-'*50}"
                    )
                    results_for_file.append(result_entry)

                    if alpha_detail.get('grade') != 'INFERIOR':
                        submit_count += 1
                        write_lines(r"C:\Users\nay\Desktop\qr\qr\worldquant\utils\logtxt\alphalist.txt", alpha_id)
                    break
                except Exception as e:
                    print(f'提交失败: {e}')
                    sleep(10)
                    try:
                        sess = sign_in()
                    except:
                        pass

    # 循环结束后，将所有结果写入一个带时间戳的文件
    if results_for_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_submit_{submit_count}.txt"
        filepath = os.path.join(result_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(results_for_file))
        print(f"🎉 本次运行结果已保存至: {filepath}")

    print(f"Total submitted alphas: {submit_count}, next start index: {next_start_index}")