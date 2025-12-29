# 生成2000个Alpha表达式的文件

alphas = []

# ============ 模板1: 价量动量类 (400个) ============
# 基于价格和成交量的动量/反转策略

price_fields = ['close', 'open', 'high', 'low', 'vwap']
volume_fields = ['volume', 'adv20']
lookbacks_short = [3, 5, 10, 15, 20]
lookbacks_medium = [20, 30, 40, 60]
groups = ['sector', 'industry', 'subindustry']

# 1.1 价格动量 rank差值
for p in price_fields:
    for lb1 in [5, 10, 20]:
        for lb2 in [3, 5, 10]:
            if lb1 != lb2:
                alphas.append(f"rank(ts_delta({p}, {lb1})) - rank(ts_delta({p}, {lb2}))")

# 1.2 价量背离
for p in price_fields:
    for v in volume_fields:
        for lb in lookbacks_short:
            alphas.append(f"rank(ts_rank({p}, {lb})) - rank(ts_rank({v}, {lb}))")
            alphas.append(f"ts_rank(rank({p}) - rank({v}), {lb})")

# 1.3 成交量加权动量
for v in volume_fields:
    for lb in lookbacks_short:
        alphas.append(f"rank(ts_sum(multiply(returns, {v}), {lb}))")
        alphas.append(f"ts_rank(divide(ts_sum(multiply(returns, {v}), {lb}), ts_sum({v}, {lb})), 20)")

# 1.4 价格突破
for p in price_fields:
    for lb in lookbacks_medium:
        alphas.append(f"rank(divide({p}, ts_mean({p}, {lb})))")
        alphas.append(f"ts_zscore({p}, {lb})")

# 1.5 均线交叉
for p in price_fields:
    for lb1 in [5, 10]:
        for lb2 in [20, 30, 60]:
            alphas.append(f"rank(subtract(ts_mean({p}, {lb1}), ts_mean({p}, {lb2})))")
            alphas.append(f"ts_rank(divide(ts_mean({p}, {lb1}), ts_mean({p}, {lb2})), 10)")

# 1.6 成交量异常
for v in volume_fields:
    for lb in lookbacks_medium:
        alphas.append(f"rank(divide({v}, ts_mean({v}, {lb})))")

# 1.7 价格范围
for lb in lookbacks_short:
    alphas.append(f"rank(divide(subtract(high, low), close))")
    alphas.append(f"ts_mean(divide(subtract(high, low), close), {lb})")
    alphas.append(f"rank(divide(subtract(close, low), add(subtract(high, low), 0.0001)))")

# 1.8 VWAP偏离
for lb in lookbacks_short:
    alphas.append(f"rank(divide(subtract(close, vwap), vwap))")
    alphas.append(f"ts_mean(divide(subtract(close, vwap), vwap), {lb})")
    alphas.append(f"ts_rank(divide(close, vwap), {lb})")

# 1.9 动量反转组合
for lb1 in [5, 10]:
    for lb2 in [20, 60]:
        alphas.append(f"subtract(ts_rank(returns, {lb1}), ts_rank(returns, {lb2}))")
        alphas.append(f"rank(subtract(ts_mean(returns, {lb1}), ts_mean(returns, {lb2})))")

# 1.10 成交量趋势
for v in volume_fields:
    for lb in lookbacks_short:
        alphas.append(f"ts_rank(ts_delta({v}, {lb}), 20)")
        alphas.append(f"rank(ts_delta(ts_mean({v}, {lb}), 5))")


# ============ 模板2: 基本面估值类 (400个) ============

fundamental_positive = ['sales', 'ebitda', 'equity', 'revenue', ]
fundamental_negative = ['debt', 'liabilities', 'cogs', 'sga_expense']
fundamental_scale = ['assets', 'enterprise_value']
backfill_periods = [90, 180, 252, 365, 504, 730]

# 2.1 盈利能力比率
for pos in fundamental_positive:
    for scale in fundamental_scale:
        for bf in backfill_periods[:3]:
            alphas.append(f"rank(divide(ts_backfill({pos}, {bf}), ts_backfill({scale}, {bf}) + 0.0001))")
            alphas.append(f"group_neutralize(rank(divide(ts_backfill({pos}, {bf}), ts_backfill({scale}, {bf}) + 0.0001)), sector)")

# 2.3 基本面动量
for field in fundamental_positive:
    for bf in backfill_periods:
        alphas.append(f"rank(ts_delta(ts_backfill({field}, {bf}), 60))")
        alphas.append(f"ts_rank(ts_backfill({field}, {bf}), 252)")

# 2.4 估值变化
for field in fundamental_positive:
    for bf in [252, 365, 504]:
        alphas.append(f"rank(divide(ts_backfill({field}, {bf}), ts_delay(ts_backfill({field}, {bf}), 60) + 0.0001))")

# 2.5 效率指标
for pos in fundamental_positive[:3]:
    for neg in fundamental_negative[:2]:
        for bf in backfill_periods[:2]:
            alphas.append(f"rank(divide(ts_backfill({pos}, {bf}), ts_backfill({neg}, {bf}) + 0.0001))")

# 2.6 规模调整基本面
for field in fundamental_positive:
    for g in groups:
        for bf in backfill_periods[:2]:
            alphas.append(f"group_neutralize(ts_rank(ts_backfill({field}, {bf}), 60), {g})")

# 2.7 资产负债比
for bf in backfill_periods[:3]:
    alphas.append(f"rank(divide(ts_backfill(equity, {bf}), ts_backfill(assets, {bf}) + 0.0001))")

# 2.9 企业价值相关
for pos in fundamental_positive:
    for bf in backfill_periods[:3]:
        alphas.append(f"rank(divide(ts_backfill({pos}, {bf}), ts_backfill(enterprise_value, {bf}) + 0.0001))")


# ============ 模板3: 分析师预期类 (300个) ============

est_fields = ['est_eps', 'est_sales', 'est_ebitda']
analyst_fields = ['anl4_buy', 'anl4_hold', 'anl4_total_rec']

# 3.1 预期动量
for est in est_fields:
    for bf in [60, 90, 120, 180, 252]:
        for lb in [20, 40, 60]:
            alphas.append(f"ts_rank(ts_backfill({est}, {bf}), {lb})")
            alphas.append(f"rank(ts_delta(ts_backfill({est}, {bf}), {lb}))")

# 3.2 预期相对价格
for est in est_fields:
    for bf in [60, 90, 180]:
        alphas.append(f"rank(divide(ts_backfill({est}, {bf}), close))")
        alphas.append(f"ts_rank(divide(ts_backfill({est}, {bf}), close), 60)")

# 3.3 分析师情绪
for lb in [10, 20, 30, 60]:
    alphas.append(f"rank(divide(anl4_buy, anl4_total_rec + 0.0001))")
    alphas.append(f"ts_rank(divide(anl4_buy, anl4_total_rec + 0.0001), {lb})")

# 3.4 预期变化率
for est in est_fields:
    for bf in [90, 180, 252]:
        for delay in [20, 40, 60]:
            alphas.append(f"rank(subtract(ts_backfill({est}, {bf}), ts_delay(ts_backfill({est}, {bf}), {delay})))")

# 3.5 预期与基本面对比
for est in ['est_sales', 'est_ebitda']:
    for fund in ['sales', 'ebitda']:
        for bf in [180, 252, 365]:
            alphas.append(f"rank(divide(ts_backfill({est}, {bf}), ts_backfill({fund}, {bf}) + 0.0001))")

# 3.6 买入评级强度
for g in groups:
    for lb in [20, 40, 60]:
        alphas.append(f"group_neutralize(ts_rank(divide(anl4_buy, anl4_total_rec + 0.0001), {lb}), {g})")

# 3.7 EPS预期相关
for bf in [60, 90, 120, 180]:
    alphas.append(f"rank(multiply(ts_backfill(est_eps, {bf}), divide(anl4_buy, anl4_total_rec + 0.0001)))")

# 3.8 分析师覆盖变化
for lb in [20, 40, 60]:
    alphas.append(f"ts_rank(anl4_total_rec, {lb})")
    alphas.append(f"rank(ts_delta(anl4_total_rec, {lb}))")


# ============ 模板4: 波动率类 (300个) ============

vol_fields = ['historical_volatility_10', 'historical_volatility_20', 'historical_volatility_30', 
              'historical_volatility_60', 'historical_volatility_90', 'historical_volatility_120',
              'historical_volatility_150', 'historical_volatility_180']
iv_fields = ['implied_volatility_mean_30', 'implied_volatility_mean_60', 'implied_volatility_mean_90',
             'implied_volatility_mean_180', 'implied_volatility_mean_360', 'implied_volatility_mean_720']


# 4.3 波动率期限结构
for i, vol1 in enumerate(vol_fields[:-1]):
    vol2 = vol_fields[i+1]
    alphas.append(f"rank(subtract({vol1}, {vol2}))")
    alphas.append(f"rank(divide({vol1}, {vol2} + 0.0001))")


# 4.7 风险调整收益
for vol in vol_fields[:4]:
    for lb in [10, 20]:
        alphas.append(f"rank(divide(ts_mean(returns, {lb}), {vol} + 0.0001))")

# 4.8 波动率均值回归
for vol in vol_fields:
    for lb in [20, 40, 60]:
        alphas.append(f"rank(subtract(ts_mean({vol}, {lb}), {vol}))")


# ============ 模板5: 情绪与新闻类 (200个) ============

# 5.1 社交情绪
for lb in [3, 5, 10, 20, 30]:
    alphas.append(f"ts_rank(scl12_sentiment, {lb})")
    alphas.append(f"rank(ts_mean(scl12_sentiment, {lb}))")
    alphas.append(f"rank(ts_delta(scl12_sentiment, {lb}))")

# 5.2 情绪动量
for lb1 in [3, 5]:
    for lb2 in [10, 20, 30]:
        alphas.append(f"subtract(ts_mean(scl12_sentiment, {lb1}), ts_mean(scl12_sentiment, {lb2}))")

# 5.3 情绪与价格
for lb in [5, 10, 20]:
    alphas.append(f"rank(multiply(scl12_sentiment, returns))")
    alphas.append(f"ts_rank(multiply(scl12_sentiment, ts_mean(returns, {lb})), 20)")

# 5.4 情绪与成交量
for v in volume_fields[:3]:
    for lb in [5, 10]:
        alphas.append(f"rank(multiply(scl12_sentiment, rank({v})))")

# 5.5 情绪标准化
for g in groups:
    for lb in [10, 20, 30]:
        alphas.append(f"group_neutralize(ts_rank(scl12_sentiment, {lb}), {g})")



# ============ 模板6: 技术因子组合类 (200个) ============

# 6.1 价格通道
for lb in [10, 20, 30, 60]:
    alphas.append(f"rank(divide(subtract(close, ts_mean(low, {lb})), subtract(ts_mean(high, {lb}), ts_mean(low, {lb})) + 0.0001))")

# 6.2 动量强度
for lb1 in [5, 10]:
    for lb2 in [20, 30, 60]:
        alphas.append(f"rank(divide(ts_sum(max(returns, 0), {lb1}), ts_sum(abs(returns), {lb1}) + 0.0001))")
        alphas.append(f"ts_rank(divide(ts_sum(max(returns, 0), {lb2}), ts_sum(abs(returns), {lb2}) + 0.0001), 20)")

# 6.3 成交量加权价格
for lb in [5, 10, 20]:
    alphas.append(f"rank(divide(close, ts_mean(vwap, {lb})))")
    alphas.append(f"ts_rank(divide(vwap, ts_mean(vwap, {lb})), 20)")

# 6.4 价格加速度
for lb in [5, 10, 20]:
    alphas.append(f"rank(ts_delta(ts_delta(close, {lb}), {lb}))")
    alphas.append(f"ts_rank(ts_delta(ts_delta(close, {lb}), 5), 20)")

# 6.5 成交量加速度
for v in volume_fields[:3]:
    for lb in [5, 10]:
        alphas.append(f"rank(ts_delta(ts_delta({v}, {lb}), {lb}))")

# 6.6 相对强弱
for lb in [10, 20, 30]:
    alphas.append(f"rank(divide(close, ts_delay(close, {lb})))")
    alphas.append(f"ts_rank(divide(close, ts_delay(close, {lb})), 60)")

# 6.7 趋势一致性
for lb in [10, 20]:
    alphas.append(f"rank(ts_sum(sign(returns), {lb}))")
    alphas.append(f"ts_rank(ts_sum(sign(returns), {lb}), 60)")

# 6.8 价量同步
for v in volume_fields[:3]:
    for lb in [5, 10, 20]:
        alphas.append(f"ts_corr(close, {v}, {lb})")
        alphas.append(f"rank(ts_corr(returns, ts_delta({v}, 1), {lb}))")


# ============ 模板7: 行业中性组合类 (200个) ============

# 7.1 中性化动量
for g in groups:
    for lb in [5, 10, 20]:
        alphas.append(f"group_neutralize(ts_rank(returns, {lb}), {g})")
        alphas.append(f"group_neutralize(rank(ts_mean(returns, {lb})), {g})")

# 7.2 中性化价值
for g in groups:
    for bf in [180, 252, 365]:
        alphas.append(f"group_neutralize(rank(divide(ts_backfill(sales, {bf}), ts_backfill(enterprise_value, {bf}) + 0.0001)), {g})")



# 7.4 中性化情绪
for g in groups:
    alphas.append(f"group_neutralize(rank(scl12_sentiment), {g})")
    alphas.append(f"group_neutralize(ts_rank(scl12_sentiment, 10), {g})")

# 7.5 中性化成交量
for g in groups:
    for v in volume_fields[:3]:
        for lb in [10, 20]:
            alphas.append(f"group_neutralize(rank(divide({v}, ts_mean({v}, {lb}))), {g})")

# 7.6 中性化基本面
for g in groups:
    for field in fundamental_positive[:3]:
        for bf in [180, 252]:
            alphas.append(f"group_neutralize(ts_rank(ts_backfill({field}, {bf}), 60), {g})")


# ============ 补充更多多样化Alpha ============

# 8.1 复合动量
for lb1 in [5, 10]:
    for lb2 in [20, 40]:
        for lb3 in [60, 120]:
            alphas.append(f"add(add(ts_rank(returns, {lb1}), ts_rank(returns, {lb2})), ts_rank(returns, {lb3}))")

# 8.2 价量比率变化
for v in volume_fields[:3]:
    for lb in [5, 10, 20]:
        alphas.append(f"ts_delta(divide(close, {v} + 0.0001), {lb})")
        alphas.append(f"rank(ts_delta(divide(close, {v} + 0.0001), {lb}))")

# 8.3 时间序列zscore
for field in ['close', 'volume', 'returns', 'vwap']:
    for lb in [20, 40, 60, 120]:
        alphas.append(f"ts_zscore({field}, {lb})")

# 8.4 延迟效应
for lb in [1, 2, 3, 5]:
    for rank_lb in [10, 20]:
        alphas.append(f"ts_rank(ts_delay(returns, {lb}), {rank_lb})")

# 8.5 非线性变换
for lb in [10, 20, 30]:
    alphas.append(f"rank(power(ts_mean(returns, {lb}), 2))")
    alphas.append(f"rank(log(divide(close, ts_delay(close, {lb})) + 1))")

# 8.6 条件组合
for lb in [10, 20]:
    alphas.append(f"multiply(sign(ts_mean(returns, {lb})), rank(volume))")
    alphas.append(f"multiply(sign(scl12_sentiment), ts_rank(returns, {lb}))")

# 8.7 衰减因子
for field in ['returns', 'volume', 'scl12_sentiment']:
    for lb in [5, 10, 20, 30]:
        alphas.append(f"ts_decay_linear({field}, {lb})")
        alphas.append(f"rank(ts_decay_linear({field}, {lb}))")

# 8.8 分位数
for field in ['close', 'volume', 'returns']:
    for lb in [20, 60, 120]:
        alphas.append(f"ts_rank({field}, {lb})")

# 8.9 相关性因子
for lb in [20, 40, 60]:
    alphas.append(f"ts_corr(close, volume, {lb})")
    alphas.append(f"ts_corr(returns, ts_delay(returns, 1), {lb})")
# 8.10 综合评分
for g in groups:
    alphas.append(f"group_neutralize(add(rank(returns), rank(scl12_sentiment)), {g})")
    alphas.append(f"group_neutralize(add(ts_rank(returns, 10), rank(divide(anl4_buy, anl4_total_rec + 0.0001))), {g})")

# 8.11 资金流向
for v in volume_fields[:3]:
    for lb in [5, 10, 20]:
        alphas.append(f"rank(ts_sum(multiply(returns, {v}), {lb}))")
        alphas.append(f"ts_rank(ts_sum(multiply(sign(returns), {v}), {lb}), 30)")

# 8.12 波动调整收益
for vol in vol_fields[:4]:
    alphas.append(f"rank(divide(returns, {vol} + 0.0001))")
    alphas.append(f"rank(divide(ts_mean(returns, 20), {vol} + 0.0001))")

# 去重并截取到2000个
alphas = list(dict.fromkeys(alphas))[:2000]

# 写入文件
with open('alphas_2000.txt', 'w') as f:
    for alpha in alphas:
        f.write(alpha + '\n')

print(f"Generated {len(alphas)} unique alphas")
