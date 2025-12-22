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
    # print(response.status_code)
    # print(response.json())
    return sess
sess = sign_in()
print(sess)

def get_datafields(
        s,
        searchScope,
        dataset_id:str = '',
        search: str = ''
):
    import pandas as pd
    instrument_type = searchScope['instrumentType']
    region = searchScope['region']
    delay = searchScope['delay']
    universe = searchScope['universe']
    if len(search) == 0:
        url_template = 'https://api.worldquantbrain.com/data-fields?' +\
            f"instrumentType={instrument_type}&region={region}&delay={delay}&universe={universe}&dataset.id={dataset_id}&limit=50"+\
            "&offset={x}"
        count = s.get(url_template.format(x=0)).json()['count']
    else:
        url_template = 'https://api.worldquantbrain.com/data-fields/search?' +\
            f"instrumentType={instrument_type}"+\
            f"&region={region}&delay={str(delay)}&universe={universe}&dataset.id={dataset_id}&limit=50"+\
            f"&search={search}"+\
            "&offset={x}"
        count = 100

    datafields_list = []
    for x in range(0, count, 50):
        datafields = s.get(url_template.format(x=x))
        datafields_list.append(datafields.json()['results'])
    datafields_list_flat = [item for sublist in datafields_list for item in sublist]
    datafields_df = pd.DataFrame(datafields_list_flat)
    return datafields_df


searchscope = {'region':'USA','delay':'1','universe':'TOP3000','instrumentType':'EQUITY'}
opt8 = get_datafields(s=sess,searchScope=searchscope,dataset_id='option8')

opt8 = opt8[opt8['type']=='MATRIX']
# print(opt8.head(2))
# print(opt8['id'].values)


# https://platform.worldquantbrain.com/ALPHA/MPA7bbL9

# 提取 Alpha ID 并获取详细参数
alpha_id = 'MPA7bbL9'
# alpha_id = 'omeNaw9v'
url = f'https://api.worldquantbrain.com/alphas/{alpha_id}'

resp = sess.get(url)
if resp.status_code == 200:
    data = resp.json()
    # 打印 Alpha 表达式
    # print("Alpha Expression:", json.dumps(data.get('regular'), indent=4))
    # 打印 仿真设置 (Settings)
    # print("Settings:", json.dumps(data.get('settings'), indent=4))
    # 打印 样本内绩效 (In-Sample Stats)
    # print("IS Stats:", json.dumps(data.get('is'), indent=4))

    # 自动判断逻辑：如果 Color 为 None，则根据指标手动判断
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
else:
    print(f"获取失败: {resp.status_code} - {resp.text}")


    # 获取到这些信息，需要，对每次的alpha_id进行判断turnover，fitness,数值以及是否pass？