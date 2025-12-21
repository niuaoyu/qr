### 将α一个个发挥服务器回测，并检查是否断线，如果断线则重连
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import logging
from datetime import datetime
logging.basicConfig(filename='simulation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# from utils.allSubmitOrNot import get_alpha_checks
from qr.worldquant.well_alpha_list.writeTxt import write_lines

from time import sleep

from main_part.sign_in import sign_in
sess = sign_in()

def save_alpha_result(result_entry, start_timestamp, result_dir):
    """
    将单个 Alpha 结果追加写入到以开始时间命名的 txt 文件中。
    """
    os.makedirs(result_dir, exist_ok=True)
    filename = f"{start_timestamp}_results.txt"
    filepath = os.path.join(result_dir, filename)
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(result_entry + "\n")
    print(f"📝 结果已追加至: {filepath}")


def send_alpha_list(sess, alpha_list):
    submit_count = 0
    next_start_index = 0

    # 获取本次运行的开始时间，用于生成唯一的文件名
    start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for alpha in alpha_list[15:]:
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

                    alpha_id = None
                    while True:
                        sim_progress_resp = sess.get(sim_progress_url)
                        # print(json.dumps(sim_progress_resp.json(), indent=4))
                        if sim_progress_resp.status_code == 401:
                            print("Token expired during polling, re-authenticating...")
                            sess = sign_in()
                            continue
                        retry_after_sec = float(sim_progress_resp.headers.get('Retry-After', '0'))
                        if retry_after_sec == 0:
                            sim_result = sim_progress_resp.json()
                            if 'alpha' not in sim_result:
                                print(f"模拟失败，响应内容: {sim_result}")
                                # 记录错误信息到文件，方便后续查看
                                result_entry = (
                                    f"Alpha ID: ERROR\n"
                                    f"Expression: {alpha.get('regular')}\n"
                                    f"Status: ERROR\n"
                                    f"Message: {sim_result.get('message', 'Unknown Error')}\n"
                                    f"{'-'*50}"
                                )
                                save_alpha_result(result_entry, start_timestamp,r"C:\Users\nay\Desktop\qr\qr\worldquant\result")
                                break  # 退出轮询循环
                            alpha_id = sim_result['alpha']
                            break
                        sleep(retry_after_sec)
                    
                    if alpha_id is None:
                        break # 退出重试循环，继续下一个 Alpha

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
                    
                    # 立即保存结果
                    save_alpha_result(result_entry, start_timestamp,r"C:\Users\nay\Desktop\qr\qr\worldquant\result")

                    if alpha_detail.get('grade') != 'INFERIOR':
                        submit_count += 1
                        write_lines(r"C:\Users\nay\Desktop\qr\qr\worldquant\well_alpha_list\alphalist.txt", alpha_id)
                    break
                except Exception as e:
                    print(f'提交失败: {e}')
                    sleep(10)
                    try:
                        sess = sign_in()
                    except:
                        pass

    print(f"Total submitted alphas: {submit_count}, next start index: {next_start_index}")