import platform
import os

import sys

# 为了能成功导入 'main_part'，需要将项目的根目录添加到 Python 的搜索路径中。
# 项目根目录 'worldquant' 是当前脚本所在目录 'ready_to_test_alpha_list' 的上一级。
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
r'''
import sys：导入 sys 模块，以便我们可以操作 Python 的路径。
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))：
这行代码会获取当前脚本的绝对路径，然后连续两次调用 os.path.dirname 来向上追溯到父目录，
最终得到 C:\Users\nay\Desktop\qr\qr\worldquant 这个项目根目录的路径。
sys.path.insert(0, project_root)：将项目根目录添加到 Python 解释器查找模块的路径列表的最前面。
这样，当你执行 from main_part.global_config ... 时，Python 就能在这个路径下找到 main_part 文件夹，并成功导入。
'''



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