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
print(project_root)
print(f"DATA_PATH: {DATA_PATH}")
INPUT_ID_FILE = os.path.join(DATA_PATH, "data", "sqlite", "all_extracted_ids.txt") 
print(f"输入 ID 文件路径: {INPUT_ID_FILE}")
print(f"数据库保存路径: {DB_PATH}")
print(f"结果保存目录: {SAVE_RESULT_DIR}")