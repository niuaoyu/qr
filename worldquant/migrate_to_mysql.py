"""
将 SQLite 数据迁移到 MySQL
在任意一台能连接 MySQL 的机器上运行
"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# 强制使用 MySQL
os.environ['DB_TYPE'] = 'mysql'

import pymysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# SQLite 源文件路径（修改为你的实际路径）
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'io', 'sqlite', 'alphas.db')


def migrate():
    # 检查 SQLite 文件
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite 文件不存在: {SQLITE_PATH}")
        return

    # 连接 SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # 连接 MySQL
    mysql_conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    mysql_cursor = mysql_conn.cursor()

    # 创建表（如果不存在）
    mysql_cursor.execute('''
        CREATE TABLE IF NOT EXISTS alpha_is (
            id              VARCHAR(64) NOT NULL,
            expression      TEXT NOT NULL,
            grade           VARCHAR(32),
            neutralization  VARCHAR(32),
            delay           INT,
            decay           INT,
            universe        VARCHAR(32),
            truncation      FLOAT,
            region          VARCHAR(32),
            nan_handling    VARCHAR(32),
            instrument_type VARCHAR(32),
            unit_handling   VARCHAR(32),
            pasteurization  INT,
            sharpe          FLOAT,
            fitness         FLOAT,
            returns         FLOAT,
            turnover        FLOAT,
            margin          FLOAT,
            pnl             BIGINT,
            drawdown        FLOAT,
            book_size       BIGINT,
            long_count      INT,
            short_count     INT,
            author          VARCHAR(128),
            date_created    VARCHAR(64),
            date_modified   VARCHAR(64),
            fingerprint     VARCHAR(128) NOT NULL PRIMARY KEY
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 读取 SQLite 数据
    sqlite_cursor.execute("SELECT * FROM alpha_is")
    rows = sqlite_cursor.fetchall()
    columns = [desc[0] for desc in sqlite_cursor.description]

    print(f"📦 SQLite 中共有 {len(rows)} 条记录")

    # 插入 MySQL
    inserted = 0
    skipped = 0
    for row in rows:
        values = tuple(row)
        placeholders = ','.join(['%s'] * len(columns))
        sql = f"INSERT IGNORE INTO alpha_is ({','.join(columns)}) VALUES ({placeholders})"
        try:
            mysql_cursor.execute(sql, values)
            if mysql_cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"⚠️ 插入失败: {e}")
            skipped += 1

    mysql_conn.commit()
    print(f"✅ 迁移完成: 插入 {inserted} 条，跳过 {skipped} 条（已存在）")

    sqlite_conn.close()
    mysql_conn.close()


if __name__ == "__main__":
    migrate()
