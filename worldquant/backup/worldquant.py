import requests
import json
from os.path import expanduser
from requests.auth import HTTPBasicAuth
import pandas as pd

with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
    credentials = json.load(f)

username,password = credentials
sess = requests.Session()
sess.auth = HTTPBasicAuth(username, password)
response = sess.post('https://api.worldquantbrain.com/authentication')
print(response.status_code)
print(response.json())

# simulation_data = {
#     'type': 'REGULAR',
#     'settings' :{
#         'instrumentType':'EQUITY',
#         'region':'USA',
#         'universe': 'TOP3000',
#         'delay' : 1,
#         'decay' : 0,
#         'neutralization' : 'INDUSTRY',
#         'truncation':  0.08,
#         'pasteurization': 'ON',
#         'unitHandling' : 'VERIFY',
#         'nanHandling' : 'OFF',
#         'language' : 'FASTEXPR',
#         'visualization': False,
#     },
#     'regular':'1 * ts_decay_linear(rank(group_neutralize(liabilities / assets, sector)), 10)'
# }
# from time import sleep
# sim_resp = sess.post('https://api.worldquantbrain.com/simulations', json=simulation_data)


# print(sim_resp.status_code, sim_resp.text, sim_resp.headers)
# sim_progress_url = sim_resp.headers.get('Location')
# if not sim_progress_url:
#     raise RuntimeError("提交失败或未返回 Location 头")


# while True:
#     sim_progress_resp = sess.get(sim_progress_url)
#     retry_after_sec = float(sim_progress_resp.headers.get('Retry-After', '0'))
#     if retry_after_sec == 0:
#         break
#     sleep(retry_after_sec)
# alpha_id = sim_progress_resp.json()['alpha']
# print(f'Alpha ID: {alpha_id}')




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
searchscope = {'region':'USA','delay':'1','universe':'Top3000','instrumentType':'EQUITY'}
fundamental6 = get_datafields(s=sess,searchScope=searchscope,dataset_id='fundamental6')
fundamental6 = fundamental6[fundamental6['type']=='MATRIX']
fundamental6.head()

datafields_list_fundamental6 = fundamental6['id'].values
datafields_list_fundamental6

alpha_list = []

for datafield in datafields_list_fundamental6:
    print('正在將alpha表达式与setting封装')
    alpha_expression = f'group_rank({datafield}/cap,subindustry)'
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
        'truncation':  0.08,
        'pasteurization': 'ON',
        'unitHandling' : 'VERIFY',
        'nanHandling' : 'ON',
        'language' : 'FASTEXPR',
        'visualization': False,
        },
    'regular':alpha_expression
    }
    alpha_list.append(simulation_data)
print(f'一共封装了 {len(alpha_list)} 个alpha表达式')



from time import sleep
for alpha in alpha_list:
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
    except :
        print(f'提交失败:等10秒后继续')
        sleep(10)