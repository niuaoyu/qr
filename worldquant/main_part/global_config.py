import platform
import os

# 获取当前系统名称 ('Windows' 或 'Linux')
system_name = platform.system()

# 获取当前文件(global_config.py)所在的绝对目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 拼接绝对路径，确保在任何地方引用都能找到正确位置
DATA_PATH = os.path.dirname(BASE_DIR)

USER = {'lab':{"name":"niuaoyula@163.com","password":"NAYnay232408."},
        'mylab':{"name":"672019598@qq.com","password":"NAYnay232408."},
        'ubuntu':{"name":"2734849800@qq.com","password":"NAYnay232408."}}
# print(f"系统名称: {system_name}")
# print(f"基础目录: {BASE_DIR}")
# print(f"数据路径: {DATA_PATH}") 
# print(f"用户配置: {USER['lab']['name'].split('@')[0]}")