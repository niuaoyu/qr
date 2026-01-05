"""
文件 input: loaders加载器、core/backtest_engine回测引擎
文件 output: 统一回测入口，只读取JSON配置
文件 pos: 项目主入口，加载JSON配置后调用回测引擎
一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config import SYSTEM_NAME, MAX_WORKERS
from core.backtest_engine import BacktestEngine
from loaders import load_from_json


# ============ 运行时配置 ============
USER_CHOICE = 'lab' 
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'batch_config.json')


def main():
    """主函数"""
    print(f"🚀 Alpha 回测系统启动 ({SYSTEM_NAME})")
    print(f"👤 账户: {USER_CHOICE}")
    print(f"📋 配置: {CONFIG_FILE}")
    print(f"💡 按 Ctrl+C 可优雅退出\n")

    # 加载配置
    payloads = load_from_json(CONFIG_FILE)
    if not payloads:
        print("⚠️ 没有生成任何任务")
        return

    # 创建引擎并执行
    engine = BacktestEngine(
        user_choice=USER_CHOICE,
        input_file_path=CONFIG_FILE,
        max_workers=MAX_WORKERS
    )
    engine.run(payloads)


if __name__ == "__main__":
    main()
