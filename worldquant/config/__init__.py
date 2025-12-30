"""
配置模块 - 统一导出所有配置项
"""
from .settings import (
    BASE_DIR,
    SYSTEM_NAME,
    IO_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    SQLITE_DIR,
    DEFAULT_ALPHA_FILE,
    DEFAULT_DB_PATH,
    DEFAULT_RESULT_PATH,
    MAX_WORKERS,
    USER,
    DEFAULT_SETTINGS,
    API_BASE_URL,
    API_AUTH_URL,
    API_SIMULATION_URL,
    API_ALPHA_URL,
    get_inferior_output_path,
    get_unknown_output_path
)

__all__ = [
    'BASE_DIR',
    'SYSTEM_NAME',
    'IO_DIR',
    'INPUT_DIR',
    'OUTPUT_DIR',
    'SQLITE_DIR',
    'DEFAULT_ALPHA_FILE',
    'DEFAULT_DB_PATH',
    'DEFAULT_RESULT_PATH',
    'MAX_WORKERS',
    'USER',
    'DEFAULT_SETTINGS',
    'API_BASE_URL',
    'API_AUTH_URL',
    'API_SIMULATION_URL',
    'API_ALPHA_URL',
    'get_inferior_output_path',
    'get_unknown_output_path'
]
