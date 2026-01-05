# storage 存储模块

> 一旦我所属的文件夹有所变化，请更新我

## 文件列表

| 文件 | 功能 |
|------|------|
| `__init__.py` | 模块入口，统一导出 |
| `database.py` | SQLite/MySQL 数据库操作 |
| `file_writer.py` | 文件写入（优质结果导出） |

---

## database.py

支持 SQLite 和 MySQL 双模式，自动根据 `.env` 中的 `DB_TYPE` 切换。

### 主要函数

```python
get_connection()      # 获取数据库连接（支持重试）
init_db()             # 初始化表结构（自动备份）
check_exists(conn, fingerprint)  # 检查指纹是否存在
save_alpha(conn, alpha_data, fingerprint)  # 保存结果
```

### 备份功能（SQLite 和 MySQL 都支持）

```python
backup_database()        # 手动备份
restore_database(path)   # 从备份恢复
list_backups()           # 列出所有备份
```

| 功能 | SQLite | MySQL |
|------|--------|-------|
| 备份方式 | 文件复制 (.bak) | SQL导出 (.sql) |
| 备份目录 | `io/sqlite/backups/` | `io/mysql_backups/` |
| 自动备份 | init_db 时 | init_db 时 |
| 备份轮转 | 保留最近5个 | 保留最近5个 |

### 配置项

```python
MAX_BACKUPS = 5           # 保留备份数量
BACKUP_ON_INIT = True     # 启动时自动备份
MYSQL_RETRY_COUNT = 3     # MySQL 连接重试次数
MYSQL_RETRY_DELAY = 2     # 重试间隔（秒）
```

### MySQL 备份文件格式

```sql
-- MySQL Backup: worldquant
-- Date: 2026-01-05T12:00:00
-- Host: 100.84.80.8

DROP TABLE IF EXISTS alpha_is;
CREATE TABLE alpha_is (...);

INSERT INTO alpha_is VALUES (...);
```

---

## file_writer.py

将结果写入TXT文件。

```python
prepend_to_file(filepath, content, lock)
```
