import requests
import json
from os.path import expanduser
from requests.auth import HTTPBasicAuth
import pandas as pd
import re
import webbrowser
import os

def sign_in():
    with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
        credentials = json.load(f)

    username,password = credentials
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    response = sess.post('https://api.worldquantbrain.com/authentication')
    print(response.status_code)
    print(response.json())
    return sess
sess = sign_in()
# print(sess)

# ---------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------
# ,'vRVrRLEb'-----submit
alpha_list = ['xAabkxVn', 'GrvOLQZG']

rows = []

print("正在获取 Alpha 数据...")

for a_id in alpha_list:
    url = f'https://api.worldquantbrain.com/alphas/{a_id}'
    try:
        data = sess.get(url).json()
        code = data.get('regular', {}).get('code', 'N/A')
        stats = data.get('is', {})
        
        # 获取各项指标
        sharpe = stats.get('sharpe')
        turnover = stats.get('turnover')
        fitness = stats.get('fitness')
        returns = stats.get('returns')
        drawdown = stats.get('drawdown')
        margin = stats.get('margin')

        # 1. Sharpe (>1.25)
        if sharpe is not None:
            if sharpe > 1.25:
                sharpe_str = f"{sharpe:.2f} <span style='color:green; font-weight:bold;'>✅</span>"
            else:
                sharpe_str = f"{sharpe:.2f} <span style='color:red; font-weight:bold;'>↓</span>"
        else:
            sharpe_str = "N/A"

        # 2. Turnover (1%-70%) -> 0.01 - 0.70
        if turnover is not None:
            if 0.01 <= turnover <= 0.70:
                turnover_str = f"{turnover:.4f} <span style='color:green; font-weight:bold;'>✅</span>"
            else:
                if turnover < 0.01:
                    turnover_str = f"{turnover:.4f} <span style='color:red; font-weight:bold;'>↓</span>"
                else:
                    turnover_str = f"{turnover:.4f} <span style='color:red; font-weight:bold;'>↑</span>"
        else:
            turnover_str = "N/A"

        # 3. Fitness (>1)
        if fitness is not None:
            if fitness > 1.0:
                fitness_str = f"{fitness:.2f} <span style='color:green; font-weight:bold;'>✅</span>"
            else:
                fitness_str = f"{fitness:.2f} <span style='color:red; font-weight:bold;'>↓</span>"
        else:
            fitness_str = "N/A"

        # 4. Returns, Drawdown, Margin
        returns_str = f"{returns:.4f}" if returns is not None else "N/A"
        drawdown_str = f"{drawdown:.4f}" if drawdown is not None else "N/A"
        margin_str = f"{margin:.6f}" if margin is not None else "N/A"
        
        row_dict = {
            'Alpha ID': a_id,
            'Expression': code,
            'Sharpe (>1.25)': sharpe_str,
            'Turnover (1%-70%)': turnover_str,
            'Fitness (>1)': fitness_str,
            'Returns': returns_str,
            'Drawdown': drawdown_str,
            'Margin': margin_str
        }
        rows.append(row_dict)
    except Exception as e:
        print(f"获取 {a_id} 失败: {e}")

# ---------------------------------------------------------
# 优化展示: 使用 Pandas 分离表达式与指标
# ---------------------------------------------------------

if rows:
    df = pd.DataFrame(rows)
    
    # 定义显示的列顺序 (不包含 Alpha ID)
    display_cols = [
        'Sharpe (>1.25)', 
        'Turnover (1%-70%)', 
        'Fitness (>1)', 
        'Returns', 
        'Drawdown', 
        'Margin'
    ]
    
    main_df = df[display_cols].copy()
    
    # 2. 生成 HTML 报告
    html_table = main_df.to_html(escape=False, index=False, classes='styled-table')
    
    # 构建表达式部分 HTML
    expr_html = ""
    for _, row in df.iterrows():
        expr_html += f"<h3>https://platform.worldquantbrain.com/alpha/{row['Alpha ID']}</h3><div class='expression-box'>{row['Expression']}</div>"

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Alpha Status Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f9f9f9; }}
            h2 {{ color: #333; border-bottom: 2px solid #009879; padding-bottom: 10px; margin-top: 30px; }}
            .styled-table {{ border-collapse: collapse; margin: 25px 0; font-size: 1.0em; min-width: 400px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.15); background-color: white; }}
            .styled-table thead tr {{ background-color: #009879; color: #ffffff; text-align: left; }}
            .styled-table th, .styled-table td {{ padding: 12px 15px; text-align: center; border: 1px solid #dddddd; }}
            .styled-table td {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; }}
            .styled-table tbody tr {{ border-bottom: 1px solid #dddddd; }}
            .styled-table tbody tr:nth-of-type(even) {{ background-color: #f3f3f3; }}
            .expression-box {{ background-color: #fff; border-left: 6px solid #009879; padding: 15px; font-family: Consolas, monospace; white-space: pre-wrap; word-wrap: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            h3 {{ color: #555; margin-top: 20px; margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h2>Alpha Metrics Overview</h2>
        {html_table}
        <h2>Alpha Expressions</h2>
        {expr_html}
    </body>
    </html>
    """
    
    output_file = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\alpha_report.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"🎉 报告已生成: {output_file}")
    webbrowser.open('file://' + output_file)
else:
    print("未获取到有效数据")
