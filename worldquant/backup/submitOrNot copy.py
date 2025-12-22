import requests
import json
from os.path import expanduser
from requests.auth import HTTPBasicAuth
import pandas as pd

def sign_in():
    with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
        credentials = json.load(f)
    username,password = credentials
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    response = sess.post('https://api.worldquantbrain.com/authentication')
    return sess
sess = sign_in()



# https://platform.worldquantbrain.com/ALPHA/MPA7bbL9

# 提取 Alpha ID 并获取详细参数

def get_alpha_checks(alpha_id):
    # alpha_id = 'MPA7bbL9'
    # alpha_id = 'omeNaw9v'
    url = f'https://api.worldquantbrain.com/alphas/{alpha_id}'
    resp = sess.get(url)
    if resp.status_code == 200:
        data = resp.json()
        stats = data.get('is', {})
        checks = stats.get('checks', [])
        for check in checks:
            name = check.get('name')
            result = check.get('result')
            value = check.get('value')
            limit = check.get('limit')
            
            # 格式化输出
            info_str = f"{name:<25} | 结果: {result}"
            if value is not None:
                info_str += f" | 当前值: {value}"
            if limit is not None:
                info_str += f" | 阈值: {limit}"
                
            print(info_str)
        print(data.get('grade'))
        return data.get('grade') != 'INFERIOR'  
    else:
        print(f"获取失败: {resp.status_code} - {resp.text}")

# get_alpha_checks('omeNaw9v')
get_alpha_checks('d5wRPPPx')