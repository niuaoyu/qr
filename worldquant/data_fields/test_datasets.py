import requests
import json
import pandas as pd
import os
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
    # 设置当前需要下载的 Universe
    current_universe = "TOPSP500"
    
    # 创建保存目录结构: .../worldquant/data_fields/TOP200/
    base_dir = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\data_fields")
    save_dir = os.path.join(base_dir, current_universe)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 已创建目录: {save_dir}")
    else:
        print(f"📁 目录已存在: {save_dir}")

    # 1. 获取该 Universe 下的所有数据集 (Data Sets)
    print(f"🔍 正在获取 {current_universe} 下的所有数据集列表...")
    datasets_url = "https://api.worldquantbrain.com/data-sets"
    ds_params = {
        "delay": 1,
        "instrumentType": "EQUITY",
        "limit": 50,
        "offset": 0,
        "region": "USA",
        "universe": current_universe
    }

    all_datasets = []
    while True:
        resp = sess.get(datasets_url, params=ds_params)
        if resp.status_code != 200:
            print(f"❌ 获取数据集列表失败: {resp.status_code} - {resp.text}")
            break
            
        data = resp.json()
        results = data.get('results', [])
        all_datasets.extend(results)
        count = data.get('count', 0)
        
        print(f"  已获取数据集清单: {len(all_datasets)} / {count}")
        if len(all_datasets) >= count:
            break
        ds_params['offset'] += 50
        time.sleep(0.2)

    print(f"✅ 共找到 {len(all_datasets)} 个数据集，开始逐个下载字段详情...\n")

    # 2. 遍历每个数据集，下载其下的所有字段
    fields_url = "https://api.worldquantbrain.com/data-fields"
    
    for i, ds in enumerate(all_datasets):
        ds_id = ds.get('id')
        ds_name = ds.get('name')
        
        print(f"[{i+1}/{len(all_datasets)}] 正在处理数据集: {ds_id} ...")
        
        # 字段请求参数
        field_params = {
            "dataset.id": ds_id,
            "delay": 1,
            "instrumentType": "EQUITY",
            "limit": 50,
            "offset": 0,
            "region": "USA",
            "universe": current_universe
        }
        
        ds_fields = []
        while True:
            f_resp = sess.get(fields_url, params=field_params)
            if f_resp.status_code != 200:
                print(f"  ❌ 获取字段失败 ({ds_id}): {f_resp.status_code}")
                break
            
            f_data = f_resp.json()
            f_results = f_data.get('results', [])
            ds_fields.extend(f_results)
            f_count = f_data.get('count', 0)
            
            if len(ds_fields) >= f_count:
                break
            field_params['offset'] += 50
            time.sleep(0.1)
            
        # 保存为 CSV
        if ds_fields:
            df = pd.DataFrame(ds_fields)
            csv_path = os.path.join(save_dir, f"{ds_id}.csv")
            df.to_csv(csv_path, index=False)
            print(f"  ✅ 已保存: {ds_id}.csv (共 {len(df)} 个字段)")
        else:
            print(f"  ⚠️ {ds_id} 没有字段或无权限")
            
    print(f"\n🎉 全部完成! 文件已保存在: {save_dir}")
