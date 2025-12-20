import requests
import json
import pandas as pd
import time
from os.path import expanduser
from requests.auth import HTTPBasicAuth

def sign_in():
    try:
        # 读取账号密码
        with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
            credentials = json.load(f)
        username, password = credentials
        
        sess = requests.Session()
        sess.auth = HTTPBasicAuth(username, password)
        
        # 发起认证请求
        response = sess.post('https://api.worldquantbrain.com/authentication')
        
        if response.status_code == 201:
            print("✅ 登录成功")
            return sess
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录过程中发生错误: {e}")
        return None

# 1. 执行登录
sess = sign_in()

if sess:
    # 2. 爬取 analyst4 所有数据
    dataset_id = "analyst4"
    api_url = "https://api.worldquantbrain.com/data-fields"
    
    # 初始参数
    params = {
        "dataset.id": dataset_id,
        "delay": 1,
        "instrumentType": "EQUITY",
        "limit": 50,
        "offset": 0,
        "region": "USA",
        "universe": "TOP200"
    }

    print(f"正在获取 {dataset_id} 的信息...")
    resp = sess.get(api_url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        count = data.get('count', 0)
        print(f"✅ 连接成功! 该数据集共有 {count} 个字段，开始全量爬取...")
        
        all_results = []
        
        # 循环分页获取
        for offset in range(0, count, 50):
            params['offset'] = offset
            print(f"  正在下载: {offset} - {min(offset+50, count)} ...")
            
            page_resp = sess.get(api_url, params=params)
            if page_resp.status_code == 200:
                results = page_resp.json().get('results', [])
                all_results.extend(results)
            else:
                print(f"❌ Offset {offset} 下载失败: {page_resp.status_code}")
            
            time.sleep(0.2)
            
        # 保存为 CSV
        if all_results:
            df = pd.DataFrame(all_results)
            save_path = expanduser(fr"C:\Users\nay\Desktop\qr\qr\worldquant\{dataset_id}_data.csv")
            df.to_csv(save_path, index=False)
            print(f"🎉 爬取完成! 共获取 {len(df)} 条数据。")
            print(f"文件已保存至: {save_path}")
            print("前5行预览:")
            print(df[['id', 'description', 'type']].head())
    else:
        print(f"❌ 获取初始信息失败: {resp.status_code}")
        print(resp.text)
