# WorldQuant Brain Alpha 回测系统

> 详细文档请查看各子模块的 md 文件

## 项目概述

- 多账户切换（lab, mylab, ubuntu, backup）
- 多线程并发回测
- 多机协作（MySQL + Tailscale）
- 自动去重（指纹检测）
- 表达式过滤

---

## 项目结构

```
worldquant/
├── main.py              # 统一入口
├── convert_txt.py       # TXT转JSON工具
├── batch_config.json    # 回测配置
├── .env                 # 敏感配置（不上传Git）
├── .env.example         # 配置模板
│
├── config/              # 配置模块 → 详见 config/config.md
├── core/                # 核心模块 → 详见 core/core.md
├── loaders/             # 加载器   → 详见 loaders/loaders.md
├── storage/             # 存储模块 → 详见 storage/storage.md
└── io/                  # 输入输出目录
```

---

## 快速开始

```bash
# 1. 配置
cp .env.example .env
# 修改 USER_CHOICE, DB_TYPE, DB_HOST

# 2. 安装依赖
pip install pymysql python-dotenv

# 3. 运行
python main.py
```

---

## 多机协作架构

### 网络拓扑

```
┌─────────────────────────────────────────────────────────────────┐
│                 Ubuntu (100.84.80.8) - MySQL主机                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MySQL Server (:3306)                   │  │
│  │                    数据库: worldquant                      │  │
│  │                    表: alpha_is (fingerprint为主键)        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │   本地 Worker      │                        │
│                    │   python main.py   │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                               │
               Tailscale VPN (100.x.x.x)
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Windows B (lab) │  │ Windows A(mylab)│  │ Ubuntu          │
│ 100.103.93.93   │  │ 100.110.126.49  │  │ 100.84.80.8     │
│                 │  │                 │  │                 │
│ python main.py  │  │ python main.py  │  │ python main.py  │
│ .env → mysql    │  │ .env → mysql    │  │ .env → mysql    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 机器角色

| 主机 | Tailscale IP | 角色 | 说明 |
|------|--------------|------|------|
| lab | 100.103.93.93 | Worker | Windows，学校有线网络 |
| mylab | 100.110.126.49 | Worker | Windows，家庭WiFi |
| ubuntu | 100.84.80.8 | MySQL主机 + Worker | Ubuntu，学校有线网络 |

### 数据流

```
1. 各机器独立加载本地 batch_config.json
2. 生成表达式 → 计算 fingerprint (表达式+设置)
3. 查询 MySQL 检查是否已存在
4. 不存在则提交回测 → 结果写入 MySQL
5. 自动去重，三机并行不冲突
```

### 跨平台设计原则

- 路径通过 `config` 模块管理，不写死
- 数据库类型通过 `.env` 切换
- git clone 后只需配置 `.env` 即可运行
- SQLite 文件可直接跨平台复制使用

---

## 模块说明

| 模块 | 文档 | 功能 |
|------|------|------|
| config | [config.md](config/config.md) | 全局配置、路径、数据库 |
| core | [core.md](core/core.md) | 回测引擎、认证、指纹、日志 |
| loaders | [loaders.md](loaders/loaders.md) | JSON加载、表达式过滤 |
| storage | [storage.md](storage/storage.md) | 数据库操作、备份 |

---

## 核心流程

1. 加载JSON配置 → 生成表达式
2. 过滤禁止模式
3. 生成指纹 → 检查数据库
4. 提交回测 → 轮询结果
5. 保存数据库 → 导出文件

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 429错误 | 自动重试，检查WQ网页端 |
| 连接超时 | 检查Tailscale网络 |
| 权限拒绝 | 检查MySQL用户授权 |

---

## 前端数据展示

详见 [front_demonstration.md](front_demonstration/front_demonstration.md)

```bash
cd front_demonstration
python server.py
# 然后浏览器打开 index.html
```

---

## 各机器 .env 配置

### Windows B (lab) - 100.103.93.93

```
USER_CHOICE=lab
DB_TYPE=mysql
DB_HOST=100.84.80.8
DB_PORT=3306
DB_USER=wq_user
DB_PASSWORD=NAYnay232408.
DB_NAME=worldquant
```

### Windows A (mylab) - 100.110.126.49

```
USER_CHOICE=mylab
DB_TYPE=mysql
DB_HOST=100.84.80.8
DB_PORT=3306
DB_USER=wq_user
DB_PASSWORD=NAYnay232408.
DB_NAME=worldquant
```

### Ubuntu - 100.84.80.8

```
USER_CHOICE=ubuntu
DB_TYPE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=wq_user
DB_PASSWORD=NAYnay232408.
DB_NAME=worldquant
```

---

## 工具脚本

| 脚本 | 功能 |
|------|------|
| `test_connection.py` | 测试数据库连接 |
| `migrate_to_mysql.py` | SQLite迁移到MySQL |
| `front_demonstration/server.py` | 前端API服务 |

---

## 数据备份

详见 [storage.md](storage/storage.md)

| 数据库 | 备份目录 | 格式 |
|--------|----------|------|
| SQLite | `io/sqlite/backups/` | .bak |
| MySQL | `io/mysql_backups/` | .sql |

- 自动备份：`init_db()` 时触发
- 备份轮转：保留最近 5 个
- 手动备份：`backup_database()`

---

## MySQL 配置（Ubuntu）

```bash
# 安装
sudo apt install mysql-server -y

# 配置远程访问
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address = 0.0.0.0

# 创建数据库和用户
sudo mysql
CREATE DATABASE worldquant CHARACTER SET utf8mb4;
CREATE USER 'wq_user'@'%' IDENTIFIED BY 'NAYnay232408.';
GRANT ALL ON worldquant.* TO 'wq_user'@'%';
FLUSH PRIVILEGES;

# 重启
sudo systemctl restart mysql
```
