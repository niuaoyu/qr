import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

csv_path = r'C:\Users\nay\Desktop\qr\qr\data\000300.XSHG_250101_251213_days.csv'
df = pd.read_csv(csv_path).loc[:,['date','prev_close','close']]
df['date'] = df['date'].astype(str).apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

# 绘制柱状图
plt.figure(figsize=(12, 8))  # 调整(12,8)可控制放大程度
# 手动调整边距（增加上下左右的空白）
plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)

plt.plot(df['date'], df['prev_close'], color='blue', label='prev_close')
plt.plot(df['date'], df['close'], color='red', label='close')
# 设置x轴范围
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 12)
plt.xlim(start_date, end_date)
plt.xticks(rotation=45)  # 标签倾斜45度
plt.tight_layout()       # 自动调整布局，避免标签拥挤/被截断
plt.xlabel('days')
plt.ylabel('Large stock points')
plt.title('prev_close and close Comparison')
# 显示图例
plt.legend()
plt.savefig(r'C:\Users\nay\Desktop\qr\qr\202512\20251212_data.png',dpi=300, bbox_inches='tight')
plt.show()