# core 核心模块

> 一旦我所属的文件夹有所变化，请更新我

## 文件列表

| 文件 | 功能 |
|------|------|
| `__init__.py` | 模块入口，统一导出 |
| `auth.py` | 登录认证（HTTPBasicAuth） |
| `fingerprint.py` | 指纹生成（SHA256） |
| `simulation.py` | 回测API调用（含429重试） |
| `backtest_engine.py` | 统一回测引擎 |
| `graceful_exit.py` | 优雅退出管理 |
| `task_logger.py` | 任务日志（实时计时） |

---

## backtest_engine.py 回测引擎

统一的回测执行入口，接收payloads列表执行多线程回测。

```python
engine = BacktestEngine(
    user_choice='lab',
    input_file_path='config.json',
    max_workers=3
)
engine.run(payloads)
```

### 并发控制策略

**Semaphore 仅控制 API 提交阶段：**
- ✅ `submit_simulation()` 在 semaphore 内部
- ✅ `poll_simulation_result()` 在 semaphore 外部
- ✅ `get_alpha_detail()` 在 semaphore 外部

**原理：**
- WorldQuant 限制的是"同时运行的回测数"，不是"轮询请求数"
- 提交成功后立即释放 semaphore，允许其他线程提交新任务
- 轮询和获取详情不占用并发配额，可以并行执行

---

## fingerprint.py 指纹生成

通过 SHA256 哈希生成唯一指纹，避免重复回测。

### 指纹组成字段
```python
key_parts = [
    expression,        # Alpha 表达式
    neutralization,    # 中性化方式
    str(delay),        # 延迟
    str(decay),        # 衰减
    universe,          # 股票池
    str(truncation),   # 截断
    region,            # 地区
    nan_handling,      # NaN 处理
    instrument_type,   # 工具类型
    unit_handling,     # 单位处理
    pasteurization     # 巴氏处理
]
fingerprint = SHA256("|".join(key_parts))
```

---

## graceful_exit.py 优雅退出

按 `Ctrl+C` 可安全退出程序，等待当前任务完成。

```python
from core import graceful

graceful.register(alpha_queue)
graceful.set_total(len(tasks))

while not graceful.is_shutdown():
    graceful.update_stats('success')

graceful.print_stats()
```

---

## task_logger.py 任务日志

实时显示任务进度和计时。

```python
task_logger.start_task(task_id, expression, settings)
task_logger.end_task(task_id, alpha_id, grade, sharpe, fitness)
task_logger.skip_task(expression, reason)
task_logger.log_error(task_id, message)
```

---

## simulation.py 429重试

WorldQuant API 限制最多 3 个并发，遇到 429 自动重试。

- 第1次：等待 10 秒
- 第2次：等待 15 秒
- 第3次：等待 20 秒
