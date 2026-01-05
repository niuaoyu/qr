"""
数据库操作模块 - 负责 Alpha 数据的存储和查询
支持：SQLite 和 MySQL，自动备份、版本轮转、恢复功能
"""
import sqlite3
import os
import shutil
import glob
import time
from datetime import datetime
from config import DEFAULT_DB_PATH, DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# MySQL 支持（可选）
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# ============ 连接配置 ============
MAX_BACKUPS = 5  # 保留最近5个备份
BACKUP_ON_INIT = True  # 初始化时自动备份
MYSQL_RETRY_COUNT = 3  # MySQL 连接重试次数
MYSQL_RETRY_DELAY = 2  # 重试间隔（秒）


def backup_database(db_path=None):
    """
    备份数据库文件

    Args:
        db_path: 数据库路径

    Returns:
        str: 备份文件路径，失败返回 None
    """
    path = db_path or DEFAULT_DB_PATH
    if not os.path.exists(path):
        return None

    # 创建备份目录
    backup_dir = os.path.join(os.path.dirname(path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = os.path.basename(path)
    backup_name = f"{db_name}.{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(path, backup_path)
        print(f"📦 数据库已备份: {backup_name}")

        # 清理旧备份（保留最近N个）
        _cleanup_old_backups(backup_dir, db_name)
        return backup_path
    except Exception as e:
        print(f"⚠️ 备份失败: {e}")
        return None


def _cleanup_old_backups(backup_dir, db_name):
    """清理旧备份，保留最近 MAX_BACKUPS 个"""
    pattern = os.path.join(backup_dir, f"{db_name}.*.bak")
    backups = sorted(glob.glob(pattern), reverse=True)

    for old_backup in backups[MAX_BACKUPS:]:
        try:
            os.remove(old_backup)
            print(f"🗑️ 清理旧备份: {os.path.basename(old_backup)}")
        except Exception:
            pass


def restore_database(backup_path, db_path=None):
    """
    从备份恢复数据库

    Args:
        backup_path: 备份文件路径
        db_path: 目标数据库路径

    Returns:
        bool: 是否恢复成功
    """
    path = db_path or DEFAULT_DB_PATH

    if not os.path.exists(backup_path):
        print(f"❌ 备份文件不存在: {backup_path}")
        return False

    try:
        # 先备份当前数据库
        if os.path.exists(path):
            backup_database(path)

        shutil.copy2(backup_path, path)
        print(f"✅ 数据库已恢复: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False


def list_backups(db_path=None):
    """列出所有备份文件"""
    path = db_path or DEFAULT_DB_PATH
    backup_dir = os.path.join(os.path.dirname(path), 'backups')
    db_name = os.path.basename(path)

    if not os.path.exists(backup_dir):
        return []

    pattern = os.path.join(backup_dir, f"{db_name}.*.bak")
    return sorted(glob.glob(pattern), reverse=True)


def get_connection(db_path=None):
    """
    获取数据库连接（支持 SQLite 和 MySQL）

    Args:
        db_path: SQLite 数据库路径（MySQL 模式下忽略）

    Returns:
        数据库连接对象
    """
    if DB_TYPE == 'mysql':
        if not MYSQL_AVAILABLE:
            raise ImportError("请安装 pymysql: pip install pymysql")

        last_error = None
        for attempt in range(MYSQL_RETRY_COUNT):
            try:
                conn = pymysql.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=10
                )
                return conn
            except Exception as e:
                last_error = e
                if attempt < MYSQL_RETRY_COUNT - 1:
                    print(f"⚠️ MySQL连接失败，{MYSQL_RETRY_DELAY}秒后重试 ({attempt+1}/{MYSQL_RETRY_COUNT}): {e}")
                    time.sleep(MYSQL_RETRY_DELAY)
        raise ConnectionError(f"MySQL连接失败，已重试{MYSQL_RETRY_COUNT}次: {last_error}")
    else:
        # SQLite 模式
        path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn


def init_db(db_path=None):
    """
    初始化数据库表和索引

    Args:
        db_path: SQLite 数据库路径（MySQL 模式下忽略）

    Returns:
        数据库连接对象
    """
    # SQLite 自动备份
    if DB_TYPE == 'sqlite':
        path = db_path or DEFAULT_DB_PATH
        if BACKUP_ON_INIT and os.path.exists(path):
            backup_database(path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    if DB_TYPE == 'mysql':
        # MySQL 建表语句
        cursor.execute('''
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
        # MySQL 索引（忽略已存在的错误）
        for idx_sql in [
            'CREATE INDEX idx_grade ON alpha_is(grade)',
            'CREATE INDEX idx_sharpe ON alpha_is(sharpe)',
            'CREATE INDEX idx_fitness ON alpha_is(fitness)'
        ]:
            try:
                cursor.execute(idx_sql)
            except Exception:
                pass  # 索引已存在，忽略
    else:
        # SQLite 建表语句
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alpha_is (
                id              TEXT NOT NULL,
                expression      TEXT NOT NULL,
                grade           TEXT,
                neutralization  TEXT,
                delay           INTEGER,
                decay           INTEGER,
                universe        TEXT,
                truncation      REAL,
                region          TEXT,
                nan_handling    TEXT,
                instrument_type TEXT,
                unit_handling   TEXT,
                pasteurization  INTEGER,
                sharpe          REAL,
                fitness         REAL,
                returns         REAL,
                turnover        REAL,
                margin          REAL,
                pnl             INTEGER,
                drawdown        REAL,
                book_size       INTEGER,
                long_count      INTEGER,
                short_count     INTEGER,
                author          TEXT,
                date_created    TEXT,
                date_modified   TEXT,
                fingerprint     TEXT NOT NULL PRIMARY KEY
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_grade ON alpha_is(grade)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sharpe ON alpha_is(sharpe DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fitness ON alpha_is(fitness DESC)')

    conn.commit()
    return conn


def check_exists(conn, fingerprint):
    """
    检查指纹是否已存在

    Args:
        conn: 数据库连接
        fingerprint: Alpha 指纹

    Returns:
        bool: 是否存在
    """
    cursor = conn.cursor()
    if DB_TYPE == 'mysql':
        cursor.execute('SELECT 1 FROM alpha_is WHERE fingerprint = %s LIMIT 1', (fingerprint,))
    else:
        cursor.execute('SELECT 1 FROM alpha_is WHERE fingerprint = ? LIMIT 1', (fingerprint,))
    return cursor.fetchone() is not None


def save_alpha(conn, alpha_data, fingerprint):
    """
    保存 Alpha 到数据库

    Args:
        conn: 数据库连接
        alpha_data: Alpha 详情数据（API返回）
        fingerprint: Alpha 指纹

    Returns:
        bool: 是否保存成功
    """
    is_data = alpha_data.get('is', {})
    settings = alpha_data.get('settings', {})
    regular = alpha_data.get('regular', {})
    expression = regular.get('code', '') if isinstance(regular, dict) else ''

    # pasteurization 转换为整数
    pasteur_val = 1 if settings.get('pasteurization') == 'ON' else 0

    columns = [
        'id', 'expression', 'grade',
        'neutralization', 'delay', 'decay', 'universe', 'truncation',
        'region', 'nan_handling', 'instrument_type', 'unit_handling', 'pasteurization',
        'sharpe', 'fitness', 'returns', 'turnover', 'margin', 'pnl', 'drawdown',
        'book_size', 'long_count', 'short_count',
        'author', 'date_created', 'date_modified', 'fingerprint'
    ]

    values = (
        alpha_data.get('id'),
        expression,
        alpha_data.get('grade'),
        settings.get('neutralization'),
        settings.get('delay'),
        settings.get('decay'),
        settings.get('universe'),
        settings.get('truncation'),
        settings.get('region'),
        settings.get('nanHandling'),
        settings.get('instrumentType'),
        settings.get('unitHandling'),
        pasteur_val,
        is_data.get('sharpe'),
        is_data.get('fitness'),
        is_data.get('returns'),
        is_data.get('turnover'),
        is_data.get('margin'),
        is_data.get('pnl'),
        is_data.get('drawdown'),
        is_data.get('bookSize'),
        is_data.get('longCount'),
        is_data.get('shortCount'),
        alpha_data.get('author'),
        alpha_data.get('dateCreated'),
        alpha_data.get('dateModified'),
        fingerprint
    )

    try:
        cursor = conn.cursor()
        if DB_TYPE == 'mysql':
            placeholders = ','.join(['%s'] * len(columns))
            sql = f"REPLACE INTO alpha_is ({','.join(columns)}) VALUES ({placeholders})"
            cursor.execute(sql, values)
        else:
            placeholders = ','.join(['?'] * len(columns))
            sql = f"INSERT OR REPLACE INTO alpha_is ({','.join(columns)}) VALUES ({placeholders})"
            conn.execute(sql, values)
        return True
    except Exception as e:
        print(f"[save_alpha] 保存失败: {e}")
        return False
