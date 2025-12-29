
"""
存储模块 - 统一管理数据库和文件存储
"""
from .database import (
    init_db,
    save_alpha,
    check_exists,
    make_fingerprint,
    get_connection
)
from .file_writer import write_quality_alpha

__all__ = [
    'init_db',
    'save_alpha',
    'check_exists',
    'make_fingerprint',
    'get_connection',
    'write_quality_alpha'
]
