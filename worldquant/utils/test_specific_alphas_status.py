import requests
import json
from os.path import expanduser
from requests.auth import HTTPBasicAuth
import pandas as pd
import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
from config import USER

# def sign_in():
#     with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
#         credentials = json.load(f)
#     username,password = credentials
#     sess = requests.Session()
#     sess.auth = HTTPBasicAuth(username, password)
#     response = sess.post('https://api.worldquantbrain.com/authentication')
#     return sess
# sess = sign_in()



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
alpha_id = 'ak3L58Zw' # good
alpha_id = 'N1o2x9gw' # inferior
# alpha_id = '78Vlvkxx' # unknown 

username,password = USER['lab']['name'],USER['lab']['password']
sess = requests.Session()
sess.auth = HTTPBasicAuth(username, password)
response = sess.post('https://api.worldquantbrain.com/authentication')
alpha_detail = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}').json()
print(f"Alpha Status: {alpha_detail.get('grade')}")
print(json.dumps(alpha_detail, indent=4))

'''
{
    "id": "ak3L58Zw",
    "type": "REGULAR",
    "author": "LH74870",
    "settings": {
        "instrumentType": "EQUITY",
        "region": "USA",
        "universe": "TOP3000",
        "delay": 1,
        "decay": 0,
        "neutralization": "MARKET",
        "truncation": 0.08,
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "maxTrade": "OFF",
        "language": "FASTEXPR",
        "visualization": false,
        "startDate": "2018-01-20",
        "endDate": "2023-01-20",
        "testPeriod": "P1Y"
    },
    "regular": {
        "code": "group_neutralize(ts_rank(rank(fnd6_newa2v1300_ppegt)/rank(enterprise_value),10),industry)",
        "description": "group_neutralize(ts_rank(rank(fnd6_newa2v1300_ppegt)/rank(enterprise_value),10),industry)",
        "operatorCount": 5
    },
    "dateCreated": "2025-12-18T20:32:36-05:00",
    "dateSubmitted": null,
    "dateModified": "2025-12-19T01:34:02-05:00",
    "name": "my ???",
    "favorite": false,
    "hidden": false,
    "color": "PURPLE",
    "category": null,
    "tags": [
        "my"
    ],
    "classifications": [
        {
            "id": "DATA_USAGE:SINGLE_DATA_SET",
            "name": "Single Data Set Alpha"
        }
    ],
    "grade": "AVERAGE",
    "stage": "IS",
    "status": "UNSUBMITTED",
    "is": {
        "pnl": 9475153,
        "bookSize": 20000000,
        "longCount": 994,
        "shortCount": 1007,
        "turnover": 0.6819,
        "returns": 0.1915,
        "drawdown": 0.0507,
        "margin": 0.000562,
        "sharpe": 2.13,
        "fitness": 1.13,
        "startDate": "2018-01-20",
        "checks": [
            {
                "name": "LOW_SHARPE",
                "result": "PASS",
                "limit": 1.25,
                "value": 2.13
            },
            {
                "name": "LOW_FITNESS",
                "result": "PASS",
                "limit": 1.0,
                "value": 1.13
            },
            {
                "name": "LOW_TURNOVER",
                "result": "PASS",
                "limit": 0.01,
                "value": 0.6819
            },
            {
                "name": "HIGH_TURNOVER",
                "result": "PASS",
                "limit": 0.7,
                "value": 0.6819
            },
            {
                "name": "CONCENTRATED_WEIGHT",
                "result": "PASS"
            },
            {
                "name": "LOW_SUB_UNIVERSE_SHARPE",
                "result": "PASS",
                "limit": 0.92,
                "value": 1.53
            },
            {
                "name": "SELF_CORRELATION",
                "result": "PENDING"
            },
            {
                "name": "MATCHES_COMPETITION",
                "result": "PASS",
                "competitions": [
                    {
                        "id": "challenge",
                        "name": "Challenge"
                    }
                ]
            }
        ]
    },
    "os": null,
    "train": {
        "pnl": 7675334,
        "bookSize": 20000000,
        "longCount": 992,
        "shortCount": 999,
        "turnover": 0.682,
        "returns": 0.1946,
        "drawdown": 0.0485,
        "margin": 0.000571,
        "fitness": 1.25,
        "sharpe": 2.34,
        "startDate": "2018-01-20"
    },
    "test": {
        "pnl": 1797360,
        "bookSize": 20000000,
        "longCount": 1002,
        "shortCount": 1041,
        "turnover": 0.6809,
        "returns": 0.1783,
        "drawdown": 0.0507,
        "margin": 0.000524,
        "fitness": 0.82,
        "sharpe": 1.6,
        "startDate": "2022-01-20"
    },
    "prod": null,
    "competitions": null,
    "themes": null,
    "pyramids": null,
    "pyramidThemes": null,
    "team": null
}
'''