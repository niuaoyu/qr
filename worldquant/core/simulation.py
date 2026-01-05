"""
回测引擎模块 - 负责 Alpha 回测任务执行
"""
import time
from config import API_SIMULATION_URL, API_ALPHA_URL

MAX_CONCURRENT = 3  # WorldQuant 平台最大并发数


def get_running_simulations(session):
    """
    获取当前运行中的回测任务数量

    Returns:
        int: 运行中的任务数，失败返回 -1
    """
    try:
        response = session.get(API_SIMULATION_URL)
        if response.status_code != 200:
            return -1
        data = response.json()
        # API 返回运行中任务列表
        if isinstance(data, list):
            return len(data)
        return data.get('count', 0)
    except Exception:
        return -1


def wait_for_slot(session, max_wait=180):
    """
    等待直到有可用的并发槽位

    Args:
        session: 登录会话
        max_wait: 最大等待时间（秒）

    Returns:
        bool: True=有槽位可用, False=超时
    """
    start = time.time()
    while time.time() - start < max_wait:
        running = get_running_simulations(session)
        if running == -1:
            # 查询失败，直接尝试提交
            return True
        if running < MAX_CONCURRENT:
            return True
        wait = min(10, max_wait - (time.time() - start))
        if wait <= 0:
            break
        print(f"\n⏳ 当前 {running}/{MAX_CONCURRENT} 任务运行中，等待 {int(wait)} 秒...")
        time.sleep(wait)
    return False


def submit_simulation(session, alpha_payload, max_retries=5):
    """
    提交回测任务（先等待槽位，支持 429 错误自动重试）

    参数:
        session: 登录会话
        alpha_payload: Alpha 配置
        max_retries: 429 错误最大重试次数
    """
    # 先等待可用槽位
    if not wait_for_slot(session):
        print(f"\n⚠️ 等待槽位超时")
        return None

    for attempt in range(max_retries + 1):
        try:
            response = session.post(API_SIMULATION_URL, json=alpha_payload)

            if response.status_code == 401:
                return None

            # 429 并发限制 - 智能等待
            if response.status_code == 429:
                if attempt < max_retries:
                    # 先查询当前任务数
                    if not wait_for_slot(session, max_wait=60):
                        wait_time = 15 + attempt * 5
                        print(f"\n⏳ 429限制，等待 {wait_time} 秒 ({attempt+1}/{max_retries})...")
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


def poll_simulation_result(session, progress_url, timeout=300):
    """
    轮询回测结果

    Args:
        session: 登录会话
        progress_url: 轮询URL
        timeout: 超时时间（秒），默认300秒

    Returns:
        str: alpha_id 或 None（失败时）
    """
    start_time = time.time()

    while True:
        # 超时检查
        if time.time() - start_time > timeout:
            print(f"\n⚠️ 轮询超时 ({timeout}秒)")
            return None

        try:
            response = session.get(progress_url)
        except Exception as e:
            print(f"\n⚠️ 轮询请求异常: {e}")
            return None

        # 401 需要重新登录
        if response.status_code == 401:
            print(f"\n⚠️ 轮询返回401，需要重新登录")
            return None

        # 非200状态码
        if response.status_code not in [200, 201, 202]:
            print(f"\n⚠️ 轮询失败 [{response.status_code}]: {response.text[:200]}")
            return None

        retry_after = float(response.headers.get('Retry-After', '0'))
        if retry_after == 0:
            try:
                result = response.json()
            except Exception as e:
                print(f"\n⚠️ JSON解析失败: {e}")
                return None

            # 检查是否有错误信息
            if 'error' in result:
                print(f"\n⚠️ 回测错误: {result.get('error')}")
                return None

            alpha_id = result.get('alpha')
            if not alpha_id:
                # 打印完整响应以便调试
                print(f"\n⚠️ 未获取到alpha_id，响应: {str(result)[:300]}")
            return alpha_id

        time.sleep(retry_after)


def get_alpha_detail(session, alpha_id):
    """获取 Alpha 详情"""
    url = f'{API_ALPHA_URL}/{alpha_id}'
    response = session.get(url)

    if response.status_code == 401:
        return None

    return response.json()
