# coding=utf-8
import requests


# Get token
# <your_username> 以及 <your_password> 换成您的认证信息
auth_url = 'https://rqdata.ricequant.com/auth'
auth_json = {'user_name': '15256832925', 'password': 'a1234567890'}
token = requests.post(auth_url, json=auth_json).text

# Get data
data_url = 'https://rqdata.ricequant.com/api'
data_json = {'method': 'get_price', 'order_book_ids': ['10001941', '10001943'], 'start_date': '20190601', 'end_date': '20191011'}
headers = {'token': token}
response = requests.post(data_url, json=data_json, headers=headers)

print('resp: ', response.text)