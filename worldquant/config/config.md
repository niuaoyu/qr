# config 配置模块

> 一旦我所属的文件夹有所变化，请更新我

## 文件列表

| 文件 | 功能 |
|------|------|
| `__init__.py` | 模块入口，统一导出配置项 |
| `settings.py` | 全局配置（路径、账号、数据库、API） |

## settings.py 配置项

### 路径配置
- `BASE_DIR` - 项目根目录
- `IO_DIR` - 输入输出目录
- `INPUT_DIR` - 待测试表达式目录
- `OUTPUT_DIR` - 结果输出目录
- `SQLITE_DIR` - SQLite数据库目录

### 数据库配置
- `DB_TYPE` - 数据库类型（sqlite/mysql）
- `DB_HOST` - MySQL主机IP
- `DB_PORT` - MySQL端口
- `DB_USER` - MySQL用户名
- `DB_PASSWORD` - MySQL密码
- `DB_NAME` - 数据库名

### 并发配置
- `MAX_WORKERS` - 最大并发数（默认3）

### 用户账户
从 `.env` 文件加载：
- `USER` - 账户字典（lab, mylab, ubuntu, backup）

### 默认回测设置
- `DEFAULT_SETTINGS` - 回测参数默认值

### API配置
- `API_BASE_URL` - WorldQuant API 基础URL
- `API_AUTH_URL` - 认证接口
- `API_SIMULATION_URL` - 回测接口
- `API_ALPHA_URL` - Alpha接口

## 输出路径生成函数

```python
get_inferior_output_path(input_file_path)  # 生成inferior结果路径
get_unknown_output_path(input_file_path)   # 生成unknown结果路径
```
