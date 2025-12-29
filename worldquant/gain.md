记录学习到的能力:
1.结构化
  config.yaml              # [新增] 替代硬编码配置 (路径、账号、阈值)
  src/
    core/                  # [纯逻辑层] 不碰数据库，不碰网络
      fingerprint.py       # 也就是目前的 make_fingerprint, norm_expr
      parser.py            # 从 API JSON 中提取 IS 字段、转换 pasteurization 等清洗逻辑
      filters.py           # 定义过滤规则 (如: grade != FAIL, Sharpe > 1.0)
    
    io/                    # [读写层] 负责与外部世界交互
      brain_api.py         # 封装 requests, 多账户轮询, 429 重试, 登录保活
      sqlite_store.py      # 也就是目前的 db_utils.py (建表, 存, 查重)
      file_loader.py       # 也就是目前的 load_alpha_ids, 扫描目录提取 ID
    
    app/                   # [应用层] 组装流水线
      pipeline.py          # 定义 Stage 接口和执行流
      tasks.py             # 具体任务: ingest_task (入库), export_task (导出)
      main.py              # 入口，读取 config，根据命令行参数调用 tasks



2.文件存档:
    archive/
        2025-12/
            tool_xxx.py
            experiment_xxx.ipynb
            note.md
    每个文件只要求加一行说明：
        用途：干什么的
        输入/输出：数据从哪来、产出是什么
        替代品：现在用哪个新脚本替代它
