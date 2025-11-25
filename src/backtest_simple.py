"""\
基于公开 ETF 收盘价（示例使用 SPY）的一段最基础回测代码。

- 读取 data/spy_sample.csv（来自公开市场数据摘录），仅包含日期与收盘价。
- 计算 5 日与 10 日简单移动均线，生成金叉/死叉信号。
- 用前一日信号决定当日持仓，评估累计收益与最大回撤。
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


def load_price_data(csv_path: Path) -> pd.DataFrame:
    """读取价格数据并生成日收益率。

    参数:
        csv_path: CSV 文件路径，需包含 `Date` 和 `Close` 列。
    返回:
        带有 `return` 列的 DataFrame，索引为日期。
    """
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.sort_values("Date").set_index("Date")
    df["return"] = df["Close"].pct_change().fillna(0.0)
    return df


def apply_ma_strategy(df: pd.DataFrame, fast: int = 5, slow: int = 10) -> pd.DataFrame:
    """为 DataFrame 添加简单均线策略信号。

    信号逻辑：当快线高于慢线时持有（1），否则空仓（0）。
    为避免未来函数，交易日持仓使用前一日的信号。
    """
    result = df.copy()
    result[f"ma_{fast}"] = result["Close"].rolling(fast).mean()
    result[f"ma_{slow}"] = result["Close"].rolling(slow).mean()
    result["signal"] = (result[f"ma_{fast}"] > result[f"ma_{slow}"]).astype(int)
    result["position"] = result["signal"].shift(1).fillna(0)
    return result


def calculate_performance(df: pd.DataFrame) -> Tuple[float, float]:
    """计算累计收益率与最大回撤。

    返回:
        cumulative_return: 最终累计收益率。
        max_drawdown: 最大回撤，负数表示回撤幅度。
    """
    df = df.copy()
    df["strategy_return"] = df["position"] * df["return"]
    df["equity_curve"] = (1 + df["strategy_return"]).cumprod()

    rolling_max = df["equity_curve"].cummax()
    drawdown = df["equity_curve"] / rolling_max - 1
    max_drawdown = drawdown.min()

    cumulative_return = df["equity_curve"].iloc[-1] - 1
    return cumulative_return, max_drawdown


def run_backtest(csv_path: Path) -> None:
    """执行回测并打印结果。"""
    price_df = load_price_data(csv_path)
    signal_df = apply_ma_strategy(price_df)
    cumulative_return, max_drawdown = calculate_performance(signal_df)

    print("===== 简单均线策略回测 =====")
    print(f"样本数据：{csv_path.name}")
    print(f"交易日数量：{len(signal_df)}")
    print(f"累计收益率：{cumulative_return:.2%}")
    print(f"最大回撤：{max_drawdown:.2%}")


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parent.parent / "data" / "spy_sample.csv"
    run_backtest(sample_path)
