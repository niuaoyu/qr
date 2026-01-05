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

# MySQL 备份目录（相对于项目根目录）
MYSQL_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'io', 'mysql_backups')


def backup_database(db_path=None):
    """
    备份数据库（支持 SQLite 和 MySQL）

    Args:
        db_path: SQLite 数据库路径（MySQL 模式下忽略）

    Returns:
        str: 备份文件路径，失败返回 None
    """
    if DB_TYPE == 'mysql':
        return _backup_mysql()
    else:
        return _backup_sqlite(db_path)


def _backup_sqlite(db_path=None):
    """SQLite 备份（文件复制）"""
    path = db_path or DEFAULT_DB_PATH
    if not os.path.exists(path):
        return None

    backup_dir = os.path.join(os.path.dirname(path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = os.path.basename(path)
    backup_name = f"{db_name}.{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(path, backup_path)
        print(f"📦 SQLite已备份: {backup_name}")
        _cleanup_old_backups(backup_dir, db_name, '.bak')
        return backup_path
    except Exception as e:
        print(f"⚠️ SQLite备份失败: {e}")
        return None


def _backup_mysql():
    """MySQL 备份（SQL导出）"""
    if not MYSQL_AVAILABLE:
        print("⚠️ pymysql 未安装，无法备份")
        return None

    os.makedirs(MYSQL_BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{DB_NAME}.{timestamp}.sql"
    backup_path = os.path.join(MYSQL_BACKUP_DIR, backup_name)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(f"-- MySQL Backup: {DB_NAME}\n")
            f.write(f"-- Date: {datetime.now().isoformat()}\n")
            f.write(f"-- Host: {DB_HOST}\n\n")

            # 导出表结构
            cursor.execute("SHOW CREATE TABLE alpha_is")
            row = cursor.fetchone()
            create_sql = row['Create Table'] if isinstance(row, dict) else row[1]
            f.write(f"DROP TABLE IF EXISTS alpha_is;\n")
            f.write(f"{create_sql};\n\n")

            # 导出数据
            cursor.execute("SELECT * FROM alpha_is")
            rows = cursor.fetchall()

            if rows:
                columns = list(rows[0].keys()) if isinstance(rows[0], dict) else None
                for row in rows:
                    if isinstance(row, dict):
                        values = [_escape_sql_value(row[col]) for col in columns]
                    else:
                        values = [_escape_sql_value(v) for v in row]
                    f.write(f"INSERT INTO alpha_is VALUES ({','.join(values)});\n")

        conn.close()
        print(f"📦 MySQL已备份: {backup_name} ({len(rows)}条记录)")
        _cleanup_old_backups(MYSQL_BACKUP_DIR, DB_NAME, '.sql')
        return backup_path

    except Exception as e:
        print(f"⚠️ MySQL备份失败: {e}")
        return None


def _escape_sql_value(value):
    """转义 SQL 值"""
    if value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        escaped = str(value).replace("'", "''").replace("\\", "\\\\")
        return f"'{escaped}'"


def _cleanup_old_backups(backup_dir, db_name, ext='.bak'):
    """清理旧备份，保留最近 MAX_BACKUPS 个"""
    pattern = os.path.join(backup_dir, f"{db_name}.*{ext}")
    backups = sorted(glob.glob(pattern), reverse=True)

    for old_backup in backups[MAX_BACKUPS:]:
        try:
            os.remove(old_backup)
            print(f"🗑️ 清理旧备份: {os.path.basename(old_backup)}")
        except Exception:
            pass


def restore_database(backup_path, db_path=None):
    """
    从备份恢复数据库（支持 SQLite 和 MySQL）

    Args:
        backup_path: 备份文件路径
        db_path: SQLite 目标数据库路径（MySQL 模式下忽略）

    Returns:
        bool: 是否恢复成功
    """
    if not os.path.exists(backup_path):
        print(f"❌ 备份文件不存在: {backup_path}")
        return False

    if DB_TYPE == 'mysql':
        return _restore_mysql(backup_path)
    else:
        return _restore_sqlite(backup_path, db_path)


def _restore_sqlite(backup_path, db_path=None):
    """SQLite 恢复"""
    path = db_path or DEFAULT_DB_PATH
    try:
        if os.path.exists(path):
            backup_database(path)
        shutil.copy2(backup_path, path)
        print(f"✅ SQLite已恢复: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ SQLite恢复失败: {e}")
        return False


def _restore_mysql(backup_path):
    """MySQL 恢复（执行SQL文件）"""
    try:
        backup_database()  # 先备份当前数据

        conn = get_connection()
        cursor = conn.cursor()

        with open(backup_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割并执行 SQL 语句
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)

        conn.commit()
        conn.close()
        print(f"✅ MySQL已恢复: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ MySQL恢复失败: {e}")
        return False


def list_backups(db_path=None):
    """列出所有备份文件（支持 SQLite 和 MySQL）"""
    if DB_TYPE == 'mysql':
        if not os.path.exists(MYSQL_BACKUP_DIR):
            return []
        pattern = os.path.join(MYSQL_BACKUP_DIR, f"{DB_NAME}.*.sql")
        return sorted(glob.glob(pattern), reverse=True)
    else:
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
    # 自动备份（SQLite 和 MySQL 都支持）
    if BACKUP_ON_INIT:
        if DB_TYPE == 'sqlite':
            path = db_path or DEFAULT_DB_PATH
            if os.path.exists(path):
                backup_database(path)
        else:
            # MySQL 备份
            try:
                backup_database()
            except Exception:
                pass  # 首次初始化时表可能不存在

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
