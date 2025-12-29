import sqlite3
import hashlib
import re
import os

def init_db(db_path):
    """初始化数据库：建表、建索引、开启WAL模式"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)

    # 性能优化
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-200000;")
    # 建表：更新后的字段顺序
    # id, expression, grade, settings..., metrics..., author, date_created, date_modified, fingerprint
    create_table_sql = """
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
        fingerprint     TEXT NOT NULL,
        PRIMARY KEY (fingerprint)
    );
    """
    conn.execute(create_table_sql)
    # 尝试添加新列（如果表已存在但缺少这些列）
    try:
        conn.execute("ALTER TABLE alpha_is ADD COLUMN date_created TEXT;")
    except sqlite3.OperationalError:
        pass  # 列已存在

    try:
        conn.execute("ALTER TABLE alpha_is ADD COLUMN date_modified TEXT;")
    except sqlite3.OperationalError:
        pass  # 列已存在

    # 索引
    conn.execute("CREATE INDEX IF NOT EXISTS ix_alpha_is_sharpe_desc ON alpha_is (sharpe DESC);")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_alpha_is_fitness_desc ON alpha_is (fitness DESC);")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_alpha_is_filter_ru ON alpha_is (region, universe);")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_alpha_is_date_created ON alpha_is (date_created DESC);")

    conn.commit()
    return conn
def norm_expr(expr: str) -> str:
    if not expr: return ""
    return re.sub(r"\s+", " ", expr.strip())

def make_fingerprint(expr: str, s: dict) -> str:
    key = "|".join([
        norm_expr(expr),
        str(s.get("neutralization", "")),
        str(s.get("delay", "")),
        str(s.get("decay", "")),
        str(s.get("universe", "")),
        str(s.get("truncation", "")),
        str(s.get("region", "")),
        str(s.get("nanHandling", "")),
        str(s.get("instrumentType", "")),
        str(s.get("unitHandling", "")),
        str(s.get("pasteurization", "")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def check_if_exists(conn, fingerprint):
    """检查指纹是否存在"""
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM alpha_is WHERE fingerprint=? LIMIT 1", (fingerprint,))
    return cursor.fetchone() is not None
def save_alpha(conn, data, fingerprint):
    """将 Alpha 数据写入数据库，支持更新已存在的记录"""
    is_data = data.get('is')
    if not is_data:
        print(f"[save_alpha] 跳过: 无 IS 数据, id={data.get('id')}")
        return False

    settings = data.get('settings', {})
    regular = data.get('regular', {})
    expr = regular.get('code', '')
    pasteur_val = 1 if settings.get('pasteurization') == 'ON' else 0

    # 获取日期字段
    date_created = data.get('dateCreated')
    date_modified = data.get('dateModified')

    # 使用显式列名插入，避免列顺序问题
    columns = [
        'id', 'expression', 'grade',
        'neutralization', 'delay', 'decay', 'universe',
        'truncation', 'region', 'nan_handling', 'instrument_type',
        'unit_handling', 'pasteurization',
        'sharpe', 'fitness', 'returns', 'turnover',
        'margin', 'pnl', 'drawdown', 'book_size',
        'long_count', 'short_count',
        'author', 'fingerprint', 'date_created', 'date_modified'
    ]

    row = (
        data.get('id'), expr, data.get('grade'),
        settings.get('neutralization'), settings.get('delay'), settings.get('decay'), settings.get('universe'),
        settings.get('truncation'), settings.get('region'), settings.get('nanHandling'), settings.get('instrumentType'),
        settings.get('unitHandling'), pasteur_val,
        is_data.get('sharpe'), is_data.get('fitness'), is_data.get('returns'), is_data.get('turnover'),
        is_data.get('margin'), is_data.get('pnl'), is_data.get('drawdown'), is_data.get('bookSize'),
        is_data.get('longCount'), is_data.get('shortCount'),
        data.get('author'), fingerprint, date_created, date_modified
    )

    try:
        sql = f"INSERT OR REPLACE INTO alpha_is ({','.join(columns)}) VALUES ({','.join(['?']*len(columns))})"
        conn.execute(sql, row)
        print(f"[save_alpha] 成功写入: id={data.get('id')}, fingerprint={fingerprint[:8]}...")
        return True
    except Exception as e:
        print(f"[save_alpha] DB Insert Error: {e}, id={data.get('id')}")
        return False

