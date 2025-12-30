# qr' road
My road to qr ! 2025年12月8日19:30:40

  # 一、项目概述

  这是一个 WorldQuant Brain Alpha 因子回测系统，主要功能：

  1. 登录 WorldQuant Brain API 平台
  2. 读取待测试的 Alpha 表达式
  3. 多线程并发提交回测任务
  4. 将结果存储到 SQLite 数据库
  5. 将优质结果（非INFERIOR/UNKNOWN）写入文本文件

  worldquant/
  ├── .env# 敏感信息（用户密码）
  ├── .gitignore                 # Git 忽略配置
  ├── main.py                    # 主入口（已重构）
  │
  ├── config/                # 配置模块
  │   ├── __init__.py
  │   └── settings.py            # 统一配置
  │
  ├── core/                      # 核心模块
  │   ├── __init__.py
  │   ├── auth.py                # 登录认证
  │   ├── fingerprint.py         # 指纹生成
  │   └── simulation.py          # 回测引擎
  │
  ├── storage/                   # 存储模块
  │   ├── __init__.py
  │   ├── database.py            # SQLite 操作（已修复BUG）
  │   └── file_writer.py         # 文件写入
  │
  ├── io/                        # 输入输出目录
  │   ├── input/                 # 待测试表达式
  │   ├── output/                # 结果输出
  │   └── sqlite/                # 数据库文件
  │
  ├── *_old.py                   # 旧文件（已重命名）
  └── ...
  
  两个主要脚本对比

  | 功能         | main.py                | batch_backtest.py      |
  |--------------|------------------------|------------------------|
  | 输入         | TXT 文件（表达式列表） | JSON 配置（模板+参数） |
  | 生成方式     | 直接读取               | 笛卡尔积组合           |
  | 数据库存储   | ✅                     | ✅                     |
  | 指纹去重     | ✅                     | ✅                     |
  | 优质结果导出 | ✅                     | ✅                     |

  ---
arrange_combine：排列组合的工具包
    \worldquant\arrange_combine\alpha_generator_config.json
        排列组合的模板
    \worldquant\arrange_combine\generate_alpha_txt.py
        模板生成对应的a表达式（无设置的配置，只是生成a表达式模板）
    \worldquant\arrange_combine\run_and_log_alphas.py
        读取alpha_generator_config.json配置，生成对应(a表达式+设置)的alpha，测试用
        功能和main.py类似，只不过main配置不变，便于大量运行
        run_and_log_alphas.py建议少量模板+设置，举例3个a+10个设置组合=3*10=30个alpha


前端展示的方式:Front_demonstration
启动server.py——打开index.html

