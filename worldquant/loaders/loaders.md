# loaders 加载器模块

> 一旦我所属的文件夹有所变化，请更新我

## 文件列表

| 文件 | 功能 |
|------|------|
| `__init__.py` | 模块入口，统一导出 |
| `json_loader.py` | JSON配置加载器 |
| `txt_to_json.py` | TXT转JSON工具 |
| `expression_filter.py` | 表达式过滤（从JSON读取规则） |
| `filter_rules.json` | 过滤规则配置文件 |

---

## json_loader.py

从JSON配置文件加载，生成payloads列表。

```python
payloads = load_from_json('batch_config.json')
```

### 支持的配置格式

```json
{
  "alpha_templates": ["表达式模板"],
  "template_params": {"field": ["close", "vwap"]},
  "settings_base": {...},
  "settings_params": {"decay": [0, 3]}
}
```

---

## txt_to_json.py

将TXT表达式文件转换为JSON配置。

```python
txt_to_json_templates('input.txt', 'output.json')
```

---

## expression_filter.py

从 `filter_rules.json` 读取规则，过滤禁止的表达式。

```python
kept, removed = filter_expressions(expressions)
```

---

## filter_rules.json 规则配置

### 添加新规则

编辑 `filter_rules.json`，添加到 `forbidden_templates` 数组：

```json
{
  "template": "模板描述",
  "regex": "正则表达式",
  "description": "说明"
}
```

### 正则表达式对照表

| 模板写法 | 正则写法 |
|----------|----------|
| `func(` | `func\\s*\\(` |
| `...` | `.*` |
| `/` | `\\/` |
| 空格可选 | `\\s*` |
