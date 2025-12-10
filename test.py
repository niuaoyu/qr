import pandas as pd
import numpy as np

df = pd.DataFrame({
                   "A": [np.nan, 1, np.nan, np.nan, 2],
                   "B": [2, np.nan, np.nan, np.nan, 4],
                   "C": [np.nan, 3, np.nan, np.nan, 5],
                   "D": [4, 5, np.nan, 8, 9]
                  })

# 后填操作
print(df.bfill()) 

# 前填操作
# print(df.ffill())
