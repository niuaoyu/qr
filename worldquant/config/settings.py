"""
全局配置模块 - 统一管理所有配置项
"""
import os
import platform
from dotenv import load_dotenv

# ============ 路径配置 ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 系统信息
SYSTEM_NAME = platform.system()

# IO 路径
IO_DIR = os.path.join(BASE_DIR, 'io')
INPUT_DIR = os.path.join(IO_DIR, 'input')
OUTPUT_DIR = os.path.join(IO_DIR, 'output')
SQLITE_DIR = os.path.join(IO_DIR, 'sqlite')

# 默认文件路径
DEFAULT_ALPHA_FILE = os.path.join(INPUT_DIR, 'ready_to_test_alpha_list','new_alphas_2000.txt')
DEFAULT_DB_PATH = os.path.join(SQLITE_DIR, 'alphas.db')
DEFAULT_RESULT_PATH = os.path.join(OUTPUT_DIR, 'alpha_list.txt')

# ============ 并发配置 ============
MAX_WORKERS = 3  # WorldQuant 平台支持最多 3 个并发

# ============ 用户账户（从环境变量加载） ============
def _get_user_config():
    """从环境变量加载用户配置"""
    return {
        'lab': {
            "name": os.getenv('LAB_USERNAME', ''),
            "password": os.getenv('LAB_PASSWORD', '')
        },
        'mylab': {
            "name": os.getenv('MYLAB_USERNAME', ''),
            "password": os.getenv('MYLAB_PASSWORD', '')
        },
        'ubuntu': {
            "name": os.getenv('UBUNTU_USERNAME', ''),
            "password": os.getenv('UBUNTU_PASSWORD', '')
        },
        'backup': {
            "name": os.getenv('BACKUP_USERNAME', ''),
            "password": os.getenv('BACKUP_PASSWORD', '')
        }
    }

USER = _get_user_config()

# ============ 默认回测设置 ============
DEFAULT_SETTINGS = {
    'instrumentType': 'EQUITY',
    'region': 'USA',
    'universe': 'TOP3000',
    'delay': 1,
    'decay': 0,
    'neutralization': 'SUBINDUSTRY',
    'truncation': 0.01,
    'pasteurization': 'ON',
    'nanHandling': 'ON',
    'unitHandling': 'VERIFY',
    'language': 'FASTEXPR',
    'visualization': False
}

# ============ API 配置 ============
API_BASE_URL = 'https://api.worldquantbrain.com'
API_AUTH_URL = f'{API_BASE_URL}/authentication'
API_SIMULATION_URL = f'{API_BASE_URL}/simulations'
API_ALPHA_URL = f'{API_BASE_URL}/alphas'


# ============ 输出路径生成函数 ============
def get_inferior_output_path(input_file_path):
    """
    根据输入文件路径生成 inferior 结果输出路径

    Args:
        input_file_path: 输入的待测α列表文件路径

    Returns:
        str: inferior 结果输出文件路径 (io/output/{输入文件名}_inferior.txt)
    """
    input_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    return os.path.join(OUTPUT_DIR, f'{input_filename}_inferior.txt')


def get_unknown_output_path(input_file_path):
    """
    根据输入文件路径生成 unknown 结果输出路径

    Args:
        input_file_path: 输入的待测α列表文件路径

    Returns:
        str: unknown 结果输出文件路径 (io/output/{输入文件名}_unknown.txt)
    """
    input_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    return os.path.join(OUTPUT_DIR, f'{input_filename}_unknown.txt')
