# WorldQuant Brain Alpha 回测系统

## 项目概述

这是一个 WorldQuant Brain 平台的 Alpha 因子回测系统，支持：
- 多账户切换（lab, mylab, ubuntu, backup）
- 多线程并发回测
- SQLite 数据库存储结果
- 自动去重（基于指纹检测）
- 优质结果自动导出

---

## 重构记录 (2024-12-29)

### 已完成的改进

| 改进项 | 说明 |
|--------|------|
| 敏感信息外置 | 密码移至 `.env` 文件 |
| 修复数据库BUG | `storage/database.py` 占位符数量已修正 |
| 统一配置管理 | 所有配置集中在 `config/settings.py` |
| 模块化重构 | 认证、回测、指纹生成分离到 `core/` |
| 添加错误日志 | `submit_simulation` 现在会显示详细错误信息 |
| **批量回测** | 新增 `batch_backtest.py` 支持模板批量生成 |
| **数据库保护** | 自动备份、版本轮转、恢复功能 |
| **优雅退出** | 支持 Ctrl+C 安全退出，不损坏数据库 |
| **任务日志** | 实时计时显示、完整表达式输出 |
| **429重试** | 并发限制自动等待重试 |
| **前端展示** | Flask API + DataTables 数据可视化 |

### 当前项目结构

```
worldquant/
├── .env                       # 敏感信息（用户密码）
├── .gitignore                 # Git 忽略配置
├── main.py                    # 统一入口（只读JSON配置）
├── batch_backtest.py          # [已废弃]
├── batch_config.json          # 回测配置文件
├── CLAUDE.md                  # 项目文档
│
├── config/                    # 配置模块
│   ├── __init__.py
│   └── settings.py            # 统一配置
│
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── auth.py                # 登录认证
│   ├── fingerprint.py         # 指纹生成
│   ├── simulation.py          # 回测API调用（含429重试）
│   ├── backtest_engine.py     # 统一回测引擎
│   ├── graceful_exit.py       # 优雅退出管理
│   └── task_logger.py         # 任务日志（实时计时）
│
├── loaders/                   # 加载器模块
│   ├── __init__.py
│   ├── json_loader.py         # JSON配置加载器（唯一）
│   └── txt_to_json.py         # TXT转JSON工具
│
├── storage/                   # 存储模块
│   ├── __init__.py
│   ├── database.py            # SQLite 操作 + 备份功能
│   └── file_writer.py         # 文件写入
│
├── front_demonstration/       # 前端展示
│   ├── index.html             # 数据可视化页面
│   └── server.py              # Flask API 服务
│
├── io/                        # 输入输出目录
│   ├── input/                 # 待测试表达式
│   ├── output/                # 结果输出
│   └── sqlite/                # 数据库文件
│       └── backups/           # 数据库备份目录
│
├── data/                      # 数据目录（保留原有）
├── utils/                     # 工具模块（保留原有）
└── backup/                    # 代码备份文件
```

---

## 使用说明

### 统一入口（main.py）

```python
# 编辑 main.py 中的配置
USER_CHOICE = 'lab'  # 账户选择
CONFIG_FILE = 'batch_config.json'  # 配置文件路径
```

```bash
python main.py
```

### 两种使用方式

**方式1：完整表达式模式**
- 有大量完整表达式（TXT文件）
- 用 `txt_to_json_templates()` 转换到 JSON
- 只变 settings

**方式2：模板挖空模式**
- 少量模板表达式（有 `{field}` 占位符）
- 字段从文件读取或直接写
- 表达式 × 字段 × settings

### TXT 转 JSON 工具

```bash
# 将 TXT 表达式转换到 JSON 配置
python convert_txt.py io/input/alphas.txt batch_config.json

# 然后执行回测
python main.py
```

### 配置账号
编辑 `.env` 文件：
```
LAB_USERNAME=xxx@xxx.com
LAB_PASSWORD=xxx
```

### 配置数据库（多机协作）

**SQLite 模式（默认，单机）**
```
DB_TYPE=sqlite
```

**MySQL 模式（多机协作）**
```
DB_TYPE=mysql
DB_HOST=192.168.1.100  # 主电脑IP
DB_PORT=3306
DB_USER=wq_user
DB_PASSWORD=xxx
DB_NAME=worldquant
```

需要先安装 pymysql：`pip install pymysql`

### 查看结果
- 数据库：`io/sqlite/alphas.db`
- 优质结果：`io/output/alpha_list.txt`
- INFERIOR结果：`io/output/{配置文件名}_inferior.txt`
- UNKNOWN结果：`io/output/{配置文件名}_unknown.txt`

---

## 核心逻辑流程

1. **加载表达式** → 从 TXT 文件读取 Alpha 表达式
2. **生成指纹** → 基于表达式+设置生成唯一指纹
3. **数据库检查** → 如果指纹已存在则跳过
4. **提交回测** → 调用 WorldQuant API
5. **保存结果** → 存入 SQLite 数据库
6. **导出优质** → 非 INFERIOR/UNKNOWN 的结果写入 TXT

---


## 关键文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | 统一入口，选择加载模式后调用回测引擎 |
| `config/settings.py` | 所有配置项（路径、账号、默认设置） |
| `core/backtest_engine.py` | 统一回测引擎，多线程执行回测任务 |
| `core/auth.py` | 登录认证（HTTPBasicAuth） |
| `core/simulation.py` | 回测提交、轮询、获取详情、429重试 |
| `core/fingerprint.py` | 指纹生成算法（SHA256） |
| `core/graceful_exit.py` | 优雅退出管理器 |
| `core/task_logger.py` | 任务日志（实时计时、完整表达式） |
| `loaders/txt_loader.py` | TXT加载器，支持表达式+Settings变体 |
| `loaders/json_loader.py` | JSON加载器，支持模板参数组合 |
| `storage/database.py` | SQLite 操作 + 备份功能 |
| `front_demonstration/server.py` | Flask API 服务 |

---

## 批量回测配置 (batch_config.json)

```json
{
    "user_choice": "lab",
    "max_workers": 3,
    "alpha_templates": [
        "group_rank(ts_delta({field}, {days}), industry)"
    ],
    "template_params": {
        "field": ["close", "vwap"],
        "days": [5, 10, 20]
    },
    "settings_base": {
        "instrumentType": "EQUITY",
        "region": "USA",
        "universe": "TOP3000",
        ...
    },
    "settings_params": {
        "decay": [0, 3, 5],
        "truncation": [0.01, 0.05]
    }
}
```

**生成逻辑**：表达式模板 × 模板参数 × 设置参数 = 最终任务数

---

## 数据库保护功能

### 自动备份
- 每次 `init_db()` 时自动备份
- 备份位置：`io/sqlite/backups/`
- 保留最近 5 个备份

### 手动操作

```python
from storage import backup_database, restore_database, list_backups

# 手动备份
backup_database()

# 查看备份列表
backups = list_backups()

# 恢复到某个备份
restore_database(backups[0])
```

### 配置项 (storage/database.py)

```python
MAX_BACKUPS = 5       # 保留备份数量
BACKUP_ON_INIT = True # 启动时自动备份
```

---

## 优雅退出功能

### 功能说明
- 按 `Ctrl+C` 可安全退出程序
- 等待当前正在执行的任务完成
- 不会损坏数据库（SQLite WAL 模式）
- 打印最终统计信息

### 实现原理 (core/graceful_exit.py)

```python
from core import graceful

# 注册队列（用于清空待处理任务）
graceful.register(alpha_queue)

# 设置总任务数
graceful.set_total(len(tasks))

# 在工作循环中检查退出标志
while not graceful.is_shutdown():
    # 处理任务...
    graceful.update_stats('success')  # 或 'failed', 'skipped'

# 捕获 Ctrl+C
try:
    # 等待线程...
except KeyboardInterrupt:
    graceful.trigger_shutdown()

# 打印统计
graceful.print_stats()
```

### 终端输出示例

```
⚠️ 收到退出信号，等待当前任务完成...
🔧 Worker-1 收到退出信号
🔧 Worker-2 收到退出信号

==================================================
📊 最终统计:
   总数: 96
   成功: 15
   跳过: 20
   失败: 3
   未处理: 58
==================================================
⚠️ 程序被中断，部分任务未完成
```

---

## 任务日志功能 (core/task_logger.py)

### 功能说明
- 完整显示 Alpha 表达式（不截断）
- 实时计时显示（每秒更新）
- 显示关键设置参数
- 任务完成时显示 Sharpe、Fitness 等指标

### 使用方法

```python
from core import task_logger

# 开始任务（启动实时计时）
task_logger.start_task(task_id, expression, settings)

# 任务完成
task_logger.end_task(
    task_id,
    alpha_id='abc123',
    grade='INFERIOR',
    sharpe=0.85,
    fitness=0.72
)

# 跳过任务
task_logger.skip_task(expression, reason="数据库已存在")

# 记录错误
task_logger.log_error(task_id, "提交失败")
```

### 终端输出示例

```
──────────────────────────────────────────────────────────────────────
▶️ [21:05:30] 开始任务
   表达式: group_rank(ts_delta(vwap, 5), industry)
   设置: {'universe': 'TOP3000', 'delay': 1, 'decay': 0, 'neutralization': 'INDUSTRY'}
   ⏱️ 运行中... 45秒
✅ 完成 | ID: abc123 | Grade: INFERIOR | Sharpe=0.85, Fitness=0.72 | ⏱️ 45.3秒

⏭️ 跳过 (数据库已存在)
   表达式: group_rank(ts_delta(close, 10), sector)
```

---

## 429 并发限制自动重试

### 功能说明
WorldQuant API 限制最多 3 个并发模拟。当遇到 429 错误时自动等待重试。

### 重试策略 (core/simulation.py)
- 第1次重试：等待 10 秒
- 第2次重试：等待 15 秒
- 第3次重试：等待 20 秒
- 最多重试 3 次

### 终端输出示例

```
⏳ 并发限制，等待 10 秒后重试 (1/3)...
⏳ 并发限制，等待 15 秒后重试 (2/3)...
✅ 完成 | ID: xxx | Grade: INFERIOR | ⏱️ 35.2秒
```

---

## 前端数据展示

### 启动服务

```bash
cd front_demonstration
python server.py
```

访问 http://localhost:5000 打开前端页面

### 功能特性
- **数据表格**：DataTables 分页、排序、搜索
- **直方图**：Sharpe、Fitness、Returns、Turnover、Drawdown 分布
- **颜色标记**：根据指标值自动着色
- **行对比**：选中多行进行指标对比
- **导出功能**：CSV 导出、PNG 截图

### API 接口

```
GET /api/alphas?id=xxx&expression=rank&limit=100&sort=date_created
GET /api/status
```

### 排序规则
- 默认按时间排序：`COALESCE(date_modified, date_created) DESC`
- 可选按 Sharpe 排序：`sharpe DESC`

---

## 指纹去重算法 (core/fingerprint.py)

### 功能说明
通过 SHA256 哈希生成唯一指纹，避免重复回测相同的 Alpha。

### 指纹组成字段
```python
key_parts = [
    expression,           # Alpha 表达式
    neutralization,       # 中性化方式
    str(delay),          # 延迟
    str(decay),          # 衰减
    universe,            # 股票池
    str(truncation),     # 截断
    region,              # 地区
    nan_handling,        # NaN 处理
    instrument_type,     # 工具类型
    unit_handling,       # 单位处理
    pasteurization       # 巴氏处理
]
fingerprint = SHA256("|".join(key_parts))
```

### 去重逻辑
1. 生成指纹 → 2. 查询数据库 → 3. 存在则跳过，不存在则回测

---

## 常见问题

### Q: 429 错误怎么办？
A: 程序会自动重试。如果持续失败，检查是否在 WQ 网页端有正在运行的模拟。

### Q: 如何恢复误删的数据库？
A: 使用 `restore_database(backup_path)` 从备份恢复。

### Q: 如何修改并发数？
A: 编辑 `config/settings.py` 中的 `MAX_WORKERS`（最大 3）。
