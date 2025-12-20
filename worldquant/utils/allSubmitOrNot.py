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



def get_alpha_checks(alpha_id,print_info=False):
    # alpha_id = 'MPA7bbL9'
    # alpha_id = 'omeNaw9v'
    url = f'https://api.worldquantbrain.com/alphas/{alpha_id}'
    resp = sess.get(url)
    if resp.status_code == 200:
        if print_info:
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

def all_submit_or_not(alpha_id_list):
    all_pass = 0
    for alpha_id in alpha_id_list:
        print(f"检查 Alpha ID: {alpha_id}")
        if not get_alpha_checks(alpha_id):
            all_pass += 0
        else:
            all_pass += 1
        print("-" * 50)
    return all_pass
list = ['A1d72Lbe', 'd5wRPPPx', 'P0EOALGJ', '2rkN2YL6', '1Y5pjnpR', 'QPdGYGNG', 'QPdGYwLg', 'pwgNdAL6']
# passed_count = all_submit_or_not(list)

# print(passed_count,len(list),passed_count/len(list))


alpha_id = 'omeNaw9v'
alpha_id = 'ak3L58Zw'
alpha_detail = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}').json()
print(f"Alpha Status: {alpha_detail.get('grade')}")
print(json.dumps(alpha_detail, indent=4))