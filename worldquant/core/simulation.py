"""
回测引擎模块 - 负责 Alpha 回测任务执行
"""
import time
from config import API_SIMULATION_URL, API_ALPHA_URL


def submit_simulation(session, alpha_payload, max_retries=3):
    """
    提交回测任务（支持 429 错误自动重试）

    参数:
        session: 登录会话
        alpha_payload: Alpha 配置
        max_retries: 429 错误最大重试次数
    """
    for attempt in range(max_retries + 1):
        try:
            response = session.post(API_SIMULATION_URL, json=alpha_payload)

            if response.status_code == 401:
                return None  # 需要重新登录，由调用方处理

            # 429 并发限制 - 等待后重试
            if response.status_code == 429:
                if attempt < max_retries:
                    wait_time = 10 + attempt * 5  # 10秒、15秒、20秒
                    print(f"\n⏳ 并发限制，等待 {wait_time} 秒后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"\n⚠️ 并发限制，重试次数已用完")
                    return None

            if response.status_code not in [200, 201, 202]:
                print(f"\n⚠️ 提交失败 [{response.status_code}]: {response.text[:200]}")
                return None

            progress_url = response.headers.get('Location')
            if not progress_url:
                print(f"\n⚠️ 未获取到 Location header: {response.text[:200]}")
                return None

            return progress_url
        except Exception as e:
            print(f"\n⚠️ 提交异常: {e}")
            return None

    return None


def poll_simulation_result(session, progress_url):
    """轮询回测结果"""
    while True:
        response = session.get(progress_url)
        if response.status_code == 401:
            return None

        retry_after = float(response.headers.get('Retry-After', '0'))
        if retry_after == 0:
            result = response.json()
            return result.get('alpha')

        time.sleep(retry_after)


def get_alpha_detail(session, alpha_id):
    """获取 Alpha 详情"""
    url = f'{API_ALPHA_URL}/{alpha_id}'
    response = session.get(url)

    if response.status_code == 401:
        return None

    return response.json()
