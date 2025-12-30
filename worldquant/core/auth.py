"""
认证模块 - 负责 WorldQuant Brain API 登录
"""
import requests
from requests.auth import HTTPBasicAuth
from config import USER, API_AUTH_URL


def sign_in(choice='lab'):
    """
    登录 WorldQuant Brain 平台

    Args:
        choice: 账户选择 ('lab', 'mylab', 'ubuntu', 'backup')

    Returns:
        requests.Session: 已认证的会话对象
    """
    if choice not in USER:
        raise ValueError(f"无效的账户选择: '{choice}'")

    username = USER[choice]['name']
    password = USER[choice]['password']

    if not username or not password:
        raise ValueError(f"账户 '{choice}' 未配置，请检查 .env 文件")

    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    response = sess.post(API_AUTH_URL)
    response.raise_for_status()

    return sess
