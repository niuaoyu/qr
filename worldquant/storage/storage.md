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

支持 SQLite 和 MySQL 双模式。

### 主要函数

```python
get_connection()      # 获取数据库连接
init_db()             # 初始化表结构
check_exists(conn, fingerprint)  # 检查指纹是否存在
save_alpha(conn, alpha_data, fingerprint)  # 保存结果
```

### 备份功能

```python
backup_database()     # 手动备份
restore_database(path)  # 恢复备份
list_backups()        # 列出备份
```

### 配置项

```python
MAX_BACKUPS = 5       # 保留备份数量
BACKUP_ON_INIT = True # 启动时自动备份
```

---

## file_writer.py

将结果写入TXT文件。

```python
prepend_to_file(filepath, content, lock)
```
