# front_demonstration 前端展示模块

> 一旦我所属的文件夹有所变化，请更新我

## 文件列表

| 文件 | 功能 |
|------|------|
| `server.py` | Flask API 服务，支持 SQLite/MySQL |
| `index.html` | 数据可视化界面 |

---

## server.py

### 数据源

根据 `.env` 中的 `DB_TYPE` 自动选择：
- `mysql` → 连接 MySQL（多机共享）
- `sqlite` → 连接本地 `io/sqlite/alphas.db`

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态页 |
| `/api/alphas` | GET | 查询 Alpha 列表 |
| `/api/status` | GET | 服务健康检查 |

### /api/alphas 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | Alpha ID 模糊搜索 |
| `expression` | string | 表达式模糊搜索 |
| `limit` | int | 返回数量限制，默认 20 |
| `sort` | string | 排序方式：`date_created`(默认) 或 `sharpe` |

### 启动命令

```bash
cd front_demonstration
python server.py
```

输出示例：
```
Starting Flask API Server...
DB_TYPE: mysql
MySQL: wq_user@100.84.80.8:3306/worldquant
```

---

## index.html

### 功能

- 数据表格（DataTables）
- 直方图（Plotly.js）
- 行选择对比
- CSV 导出
- PNG 导出

### 数据来源

通过 AJAX 请求 `http://localhost:5001/api/alphas` 获取数据。

**注意**：必须先启动 `server.py`，否则页面无法加载数据。

### 颜色规则

| 指标 | 绿色 | 蓝色 | 紫色 | 红色 |
|------|------|------|------|------|
| Sharpe | >1.25 | 1~1.25 | 0~1 | <0 |
| Fitness | >1 | 0.8~1 | - | <0.8 |
| Turnover | 0.01~0.7 | - | <0.01 | >0.7 |

---

## 使用流程

```
1. 启动 server.py
2. 浏览器打开 index.html
3. 点击"查询数据"按钮
```

---

## 依赖

```bash
pip install flask pymysql python-dotenv
```
