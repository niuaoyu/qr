import pandas as pd

def get_row_to_df(csv_path, row_index):
    df = pd.read_csv(csv_path)
    # 检查行索引是否有效
    if row_index < 0 or row_index >= len(df):
        raise IndexError('Invalid row index')
    single_row_df = df.iloc[[row_index]]
    print(len(df),len(df.columns))
    print(df.iloc[:,[row_index,row_index+1]])
    print(df.loc[:,['prev_close','close']])
    
    return single_row_df
# def get_col_to_df(csv_path, col_index):
#     df = pd.read_csv(csv_path)
#     # 检查行索引是否有效
#     if col_index < 0 or col_index >= len(df[0]):
#         raise IndexError('Invalid rol index')
#     col_df = df.iloc[col_index]
#     return col_df

csv_file_path = r'C:\Users\nay\Desktop\qr\qr\data\000001.XSHE_250101_251213_days.csv'
row_number = 3  # 假设要获取第4行数据（索引从0开始）
result_df = get_row_to_df(csv_file_path, row_number)
# result_df = get_col_to_df(csv_file_path, row_number)
print(result_df)

