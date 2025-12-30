import pymysql

try:
    conn = pymysql.connect(
        host='202.194.67.200',
        port=3306,
        user='wq_user',
        password='NAYnay232408.',
        database='worldquant'
    )
    print("✅ MySQL 连接成功！")
    conn.close()
except Exception as e:
    print(f"❌ 连接失败: {e}")