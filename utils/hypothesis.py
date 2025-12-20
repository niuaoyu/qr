import pandas as pd

FILE = r"C:\Users\nay\Desktop\qr\qr\utils\510300.XSHG.csv"

df = pd.read_csv(FILE, encoding="utf-8-sig")
df = df.rename(columns={"Unnamed: 0": "order_book_id", "Unnamed: 1": "date"})
df = df.drop(columns=["order_book_id"])
# 关键：丢掉那行“索引名行”
print(type(df['date'][0]))
print(df["date"].head())
print(df["date"].astype(str).str.lower().head())
print(df["date"].astype(str).str.lower().ne("date").head())

df = df[df["date"].astype(str).str.lower().ne("date")].copy()
df["date"] = pd.to_datetime(df["date"].str.strip(), format="%m/%d/%Y", errors="coerce")

# 示例：如果没有概率列，这里随便填一个 0.55 做演示；实际应来自你的预测模型/手工输入
if "prob_up" not in df.columns:
    df["prob_up"] = 0.55  # TODO: 换成你的预测概率

# 实际结果：今日收盘与昨日收盘相比，涨=1，否则=0
df["realized_up"] = (df["close"] > df["prev_close"]).astype(int)

# 计算 Brier Score
df["brier_score"] = (df["prob_up"] - df["realized_up"]) ** 2

print(df)
