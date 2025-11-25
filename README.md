# quantitative_research

一个极简示例，展示如何基于公开的 ETF 收盘价数据（SPY 摘录）完成最基础的回测：

- **数据**：`data/spy_sample.csv` 为公开市场数据的节选，包含日期与收盘价。
- **策略**：5 日与 10 日简单移动均线金叉进场、死叉空仓。
- **风险控制**：使用前一日信号决定当日持仓，计算累计收益与最大回撤。

## 快速运行

```bash
pip install pandas
python src/backtest_simple.py
```

输出示例：

```
===== 简单均线策略回测 =====
样本数据：spy_sample.csv
交易日数量：31
累计收益率：X.XX%
最大回撤：Y.YY%
```

> 提示：如需验证其他公开数据集，替换 `data/spy_sample.csv` 路径即可。
