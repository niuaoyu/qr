"""
数据库操作模块 - 负责 Alpha 数据的存储和查询
"""
import sqlite3
import hashlib
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'io', 'sqlite', 'alphas.db')


def get_connection():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alpha_is (
            id TEXT NOT NULL,
            expression TEXT NOT NULL,
            grade TEXT,
            neutralization TEXT,
            delay INTEGER,
            decay INTEGER,
            universe TEXT,
            truncation REAL,
            region TEXT,
            nan_handling TEXT,
            instrument_type TEXT,
            unit_handling TEXT,
            pasteurization TEXT,
            sharpe REAL,
            fitness REAL,
            returns REAL,
            turnover REAL,
            margin REAL,
            pnl REAL,
            drawdown REAL,
            book_size REAL,
            long_count INTEGER,
            short_count INTEGER,
            author TEXT,
            fingerprint TEXT NOT NULL PRIMARY KEY
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_grade ON alpha_is(grade)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sharpe ON alpha_is(sharpe)')
    conn.commit()
    conn.close()


def make_fingerprint(expression, settings):
    """生成唯一指纹用于去重"""
    key_str = f"{expression}|{settings.get('universe')}|{settings.get('delay')}|{settings.get('decay')}|{settings.get('neutralization')}"
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]


def check_exists(fingerprint):
    """检查指纹是否已存在"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM alpha_is WHERE fingerprint = ?', (fingerprint,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def save_alpha(alpha_data):
    """保存 Alpha 到数据库"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO alpha_is 
        (id, expression, grade, neutralization, delay, decay, universe, truncation,
         region, nan_handling, instrument_type, unit_handling, pasteurization,
         sharpe, fitness, returns, turnover, margin, pnl, drawdown, 
         book_size, long_count, short_count, author, fingerprint)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        alpha_data.get('id'),
        alpha_data.get('expression'),
        alpha_data.get('grade'),
        alpha_data.get('neutralization'),
        alpha_data.get('delay'),
        alpha_data.get('decay'),
        alpha_data.get('universe'),
        alpha_data.get('truncation'),
        alpha_data.get('region'),
        alpha_data.get('nan_handling'),
        alpha_data.get('instrument_type'),
        alpha_data.get('unit_handling'),
        alpha_data.get('pasteurization'),
        alpha_data.get('sharpe'),
        alpha_data.get('fitness'),
        alpha_data.get('returns'),
        alpha_data.get('turnover'),
        alpha_data.get('margin'),
        alpha_data.get('pnl'),
        alpha_data.get('drawdown'),
        alpha_data.get('book_size'),
        alpha_data.get('long_count'),
        alpha_data.get('short_count'),
        alpha_data.get('author'),
        alpha_data.get('fingerprint')
    ))
    
    conn.commit()
    conn.close()
