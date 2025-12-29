"""
配置模块
"""
from .settings import (
    MAX_WORKERS,
    alpha_queue,
    simulation_semaphore,
    DEFAULT_SETTINGS,
    USER
)

__all__ = [
    'MAX_WORKERS',
    'alpha_queue', 
    'simulation_semaphore',
    'DEFAULT_SETTINGS',
    'USER'
]
