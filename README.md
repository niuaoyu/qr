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
  ├── main.py                    # 主入口
  ├── config/
  │   ├── __init__.py
  │   └── settings.py            # 统一配置（路径、并发、默认设置）
  │
  ├── core/
  │   ├── __init__.py
  │├── auth.py                # 登录认证
  │   ├── simulation.py          # 回测引擎
  │   └── fingerprint.py         # 指纹生成
  │
  ├── storage/
  │   ├── __init__.py
  │   ├── database.py            # SQLite操作
  │   └── file_writer.py         # 文件写入
  │
  ├── utils/
  │   ├── __init__.py
  │   ├── alpha_generator.py     # Alpha表达式生成
  │   └── report_generator.py    # HTML报告生成
  │
  ├── io/                        # 输入输出目录
  │   ├── input/ # 待测试表达式
  │   ├── output/                # 结果输出
  │   └── sqlite/                # 数据库文件
  │
  ├── data/      # 静态数据
  │   └── data_fields/           # 数据字段定义
  │
  ├── .env                       # 环境变量（敏感信息）
  └── .gitignore

arrange_combine：排列组合的工具包
    \worldquant\arrange_combine\alpha_generator_config.json
        排列组合的模板
    \worldquant\arrange_combine\generate_alpha_txt.py
        模板生成对应的a表达式（无设置的配置，只是生成a表达式模板）
    \worldquant\arrange_combine\run_and_log_alphas.py
        读取alpha_generator_config.json配置，生成对应(a表达式+设置)的alpha，测试用
        功能和main.py类似，只不过main配置不变，便于大量运行
        run_and_log_alphas.py建议少量模板+设置，举例3个a+10个设置组合=3*10=30个alpha
    
回测的方式：
    1.读取成千txt（组合1-2不同setting）——main.py——结果
    2.读取特定a表达式（组合5-10不同setting）——run_and_log_alphas.py——结果

前端展示的方式：启动server.py——打开index.html

