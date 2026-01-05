"""
文件 input: loaders加载器、core/backtest_engine回测引擎
文件 output: 统一回测入口，只读取JSON配置
文件 pos: 项目主入口，加载JSON配置后调用回测引擎
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import os
