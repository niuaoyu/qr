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

# opt8 = get_datafields(s=sess,searchScope=searchscope,dataset_id='option8')
# opt8 = opt8[opt8['type']=='MATRIX']
# opt8.head()
# datafields_list_opt8 = opt8['id'].values
# datafields_list_opt8
# fundamental6 = get_datafields(s=sess,searchScope=searchscope,dataset_id='fundamental6')
# fundamental6 = fundamental6[fundamental6['type']=='MATRIX']
# fundamental6.head()
# datafields_list_fundamental6 = fundamental6['id'].values
# datafields_list_fundamental6

import re
# template = 'group_neutralize(ts_rank(rank({vo_alias})/rank(enterprise_value),10),industry)'

# alpha_expressions = []
# for field in datafields_list_fundamental6:
#     alpha_expression = template.format(vo_alias=field)
#     alpha_expressions.append(alpha_expression)
# print('total alpha expressions:', len(alpha_expressions))
# for expr in alpha_expressions:
#     print(expr)

from qr.worldquant.io.load_alpha_expressions import load_alpha_expressions
alpha_expressions = load_alpha_expressions()
print('total alpha expressions:', len(alpha_expressions))
for expr in alpha_expressions:
    print(expr)

alpha_list = []
for alpha_expression in alpha_expressions:
    # print('正在將alpha表达式与setting封装')
    print(alpha_expression)
    simulation_data = {
    'type': 'REGULAR',
    'settings' :{
        'instrumentType':'EQUITY',
        'region':'USA',
        'universe': 'TOP3000',
        'delay' : 1,
        'decay' : 0,
        'neutralization' : 'SUBINDUSTRY',
        'truncation':  0.01,
        'pasteurization': 'ON',
        'unitHandling' : 'VERIFY',
        'nanHandling' : 'ON',
        'language' : 'FASTEXPR',
        'visualization': False,
        },
    'regular':alpha_expression
    }
    alpha_list.append(simulation_data)

alpha_list[1]

### 将α一个个发挥服务器回测，并检查是否断线，如果断线则重连
import logging
logging.basicConfig(filename='simulation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# from utils.allSubmitOrNot import get_alpha_checks
from qr.worldquant.select_alpha_list.writeTxt import write_lines
submit_count = 0
next_start_index = 0
from time import sleep
for alpha in alpha_list:
    next_start_index += 1

    sim_resp = sess.post(
        'https://api.worldquantbrain.com/simulations',
        json=alpha
    )
    try:
        sim_progress_url = sim_resp.headers.get('Location')
        while True:
            sim_progress_resp = sess.get(sim_progress_url)
            retry_after_sec = float(sim_progress_resp.headers.get('Retry-After', '0'))
            if retry_after_sec == 0:
                break
            sleep(retry_after_sec)
        alpha_id = sim_progress_resp.json()['alpha']
        print(f'Alpha ID: {alpha_id}')

        # 获取 Alpha 的详细结果状态
        alpha_detail = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}').json()
        print(f"Alpha Status: {alpha_detail.get('grade')}")
        if alpha_detail.get('grade') != 'INFERIOR':
            submit_count += 1
            write_lines(r"C:\Users\nay\Desktop\qr\qr\worldquant\utils\logtxt\alphalist.txt", alpha_id)

    except Exception as e:
        print(f'提交失败: {e}')
        sleep(2)
print(f'下一个起始值',next_start_index)