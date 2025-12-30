import platform
import os
import sys
import json
import time
import requests
from requests.auth import HTTPBasicAuth
# 1. 环境适配与路径设置
# 假设本脚本位于 c:\qr\qr\worldquant\sqlite\
# 我们需要将项目根目录加入 path，以便导入 main_part
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from global_config import DATA_PATH, USER

# 引入拆分出的数据库模块
from db_utils import init_db, make_fingerprint, check_if_exists, save_alpha

# --- 配置区域 ---
# USER_CHOICE = 'lab'  # 已改为多账户自动切换
DB_NAME = "alphas.db"

# 结果保存目录 (Windows/Linux 通用)
SAVE_RESULT_DIR = os.path.join(DATA_PATH, "data", "sqlite")
DB_PATH = os.path.join(SAVE_RESULT_DIR, DB_NAME)

# 输入的 ID 文件路径 (请确保此文件存在，每行一个 Alpha ID)
# 默认假设在 DATA_PATH 下，你可以根据实际情况修改文件名
INPUT_ID_FILE = os.path.join(DATA_PATH, "data", "sqlite", "all_extracted_ids.txt") 

# 全局 Session 缓存
SESSIONS = {}

def get_session(user_choice):
    """使用 HTTPBasicAuth 显式登录，参考 test_specific_alphas_status.py"""
    if user_choice in SESSIONS:
        return SESSIONS[user_choice]

    username = USER[user_choice]['name']
    password = USER[user_choice]['password']
    print(f"正在登录用户: {user_choice} ...")
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    resp = sess.post('https://api.worldquantbrain.com/authentication')
    if not resp.ok:
        print(f"用户 {user_choice} 登录失败: {resp.status_code}")
        return None
        
    SESSIONS[user_choice] = sess
    return sess

def load_alpha_ids(file_path):
    """从 txt 文件读取 Alpha ID"""
    if not os.path.exists(file_path):
        print(f"错误: 找不到输入文件 {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    unique_ids = list(set(ids))
    print(f"从 {file_path} 读取到 {len(unique_ids)} 个唯一的 Alpha ID")
    return unique_ids

def fetch_alpha_data_multi_user(alpha_id, user_list):
    """遍历用户列表尝试获取数据"""
    print(f"[fetch] 开始获取 {alpha_id}...")  # 添加这行
    for user in user_list:
        sess = get_session(user)
        if not sess: 
            print(f"[fetch] 用户 {user} session 为空，跳过")  # 添加
            continue
        
        try:
            url = f'https://api.worldquantbrain.com/alphas/{alpha_id}'
            print(f"[fetch] 使用用户 {user} 请求 {alpha_id}...")  # 添加
            resp = sess.get(url, timeout=30)
            print(f"[fetch] 响应状态码: {resp.status_code}")  # 添加
            
            if resp.status_code == 429:
                print(f"用户 {user} 触发速率限制 (429)，暂停 10 秒...")
                time.sleep(10)
                resp = sess.get(url, timeout=30)
            
            if resp.status_code == 200:
                print(f"[fetch] 成功获取 {alpha_id}")  # 添加
                print(f"[fetch] 响应内容: {resp.text[:100]}...")  # 添加，打印前100字符
                return resp.json()
            
            print(f"[fetch] 用户 {user} 返回 {resp.status_code}，尝试下一个用户")  # 添加
            
        except Exception as e:
            print(f"用户 {user} 请求异常: {e}")
    print(f"[fetch] 所有用户都无法获取 {alpha_id}")  # 添加
    return None


def process_alphas(alpha_id_list, conn, user_list):
    """核心循环：获取 -> 清洗 -> 入库"""
    cursor = conn.cursor()
    count = 0
    total = len(alpha_id_list)
    
    print(f"开始处理 {total} 个 Alpha...")
    
    for idx, alpha_id in enumerate(alpha_id_list):
        try:
            data = fetch_alpha_data_multi_user(alpha_id, user_list)
            
            if not data:
                print(f"[{idx+1}/{total}] 所有账户获取失败 {alpha_id}")
                continue
            
            # 1. 检查是否有 IS 结果，没有则跳过
            is_data = data.get('is')
            if not is_data:
                # print(f"[{idx+1}/{total}] 跳过 {alpha_id}: 无 IS 结果")
                continue
            
            # 2. 提取数据
            settings = data.get('settings', {})
            regular = data.get('regular', {})
            expr = regular.get('code', '')
            
            # 3. 计算指纹
            fp = make_fingerprint(expr, settings)
            
            # 4. 查重：为了更新 dateCreated 等信息，这里不再跳过已存在的记录
            # if check_if_exists(conn, fp):
            #     # print(f"[{idx+1}/{total}] 跳过 {alpha_id}: 数据库已存在相同策略")
            #     continue

            # 5. 入库：不存在则保存
            # 注意：save_alpha 内部会再次检查是否有 IS 数据
            if save_alpha(conn, data, fp):
                count += 1
                # 批量提交，每 50 条写一次盘
                if count % 50 == 0:
                    conn.commit()
                    print(f"[{idx+1}/{total}] 已入库 {count} 条...")
            
            # 稍微休眠一下，避免被检测为机器人
            time.sleep(0.1)
                
        except Exception as e:
            print(f"[{idx+1}/{total}] 处理异常 {alpha_id}: {e}")
            
    # 最后提交剩余的数据
    conn.commit()
    print(f"处理完成。共入库/更新: {count} 条。")

# --- 主程序入口 ---

if __name__ == "__main__":
    print(f"数据库路径: {DB_PATH}")
    
    # 1. 初始化数据库
    conn = init_db(DB_PATH)
    
    # 2. 读取 ID
    alpha_ids = load_alpha_ids(INPUT_ID_FILE)
    
    # 获取所有可用用户列表
    available_users = list(USER.keys())
    print(f"可用账户列表: {available_users}")

    if alpha_ids:
        try:
            # 4. 开始处理
            process_alphas(alpha_ids, conn, available_users)
            
        except Exception as e:
            print(f"登录或执行失败: {e}")
            print(f"执行失败: {e}")
    else:
        print("未找到待处理的 Alpha ID。请检查 INPUT_ID_FILE 配置。")
        
    conn.close()
