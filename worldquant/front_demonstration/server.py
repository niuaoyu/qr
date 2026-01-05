import os
import sys
from flask import Flask, request, jsonify, g
import traceback

# -----------------------------------------------------------------------------
# 1. 环境与路径配置
# -----------------------------------------------------------------------------
current_file = os.path.abspath(__file__)
api_dir = os.path.dirname(current_file)
worldquant_dir = os.path.dirname(api_dir)

sys.path.insert(0, worldquant_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(worldquant_dir, '.env'))

from config import DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SQLITE_DIR

# MySQL 支持
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

import sqlite3


# -----------------------------------------------------------------------------
# 2. Flask 应用初始化
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

DB_PATH = os.path.join(SQLITE_DIR, "alphas.db")

# -----------------------------------------------------------------------------
# 3. 数据库连接管理
# -----------------------------------------------------------------------------
def get_db():
    """获取数据库连接（支持 SQLite 和 MySQL）"""
    db = getattr(g, '_database', None)
    if db is None:
        if DB_TYPE == 'mysql':
            if not MYSQL_AVAILABLE:
                return None
            db = g._database = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            if not os.path.exists(DB_PATH):
                return None
            db = g._database = sqlite3.connect(DB_PATH)
            db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """请求结束时关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
# -----------------------------------------------------------------------------
# 4. API 路由与查询逻辑
# -----------------------------------------------------------------------------
@app.after_request
def after_request(response):
    """配置 CORS，允许跨域访问"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return "WorldQuant Alpha Server is Running! Access <a href='/api/alphas'>/api/alphas</a> to see data."

@app.route('/api/alphas', methods=['GET'])
def get_alphas():
    """
    查询 Alpha 记录接口
    
    参数:
    - id: (可选) Alpha ID 精确或模糊搜索
    - expression: (可选) 表达式模糊搜索关键词
    - limit: (可选) 返回记录数量限制，默认 20
    - sort: (可选) 排序方式，date_created(默认) 或 sharpe
    """
    db = get_db()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    # 获取查询参数
    id_query = request.args.get('id', '').strip()
    expression_query = request.args.get('expression', '').strip()
    sort_by = request.args.get('sort', 'date_created').strip()
    try:
        limit = int(request.args.get('limit', 20))
    except ValueError:
        limit = 20

    # 占位符（MySQL用%s，SQLite用?）
    ph = '%s' if DB_TYPE == 'mysql' else '?'

    # 构建 SQL 查询
    query_sql = """
        SELECT
            id, expression, grade,
            neutralization, delay, decay, universe, truncation, region,
            nan_handling, instrument_type, unit_handling, pasteurization,
            sharpe, fitness, returns, turnover, margin, pnl, drawdown,
            book_size, long_count, short_count,
            author, date_created, date_modified, fingerprint,
            COALESCE(date_modified, date_created) as latest_date
        FROM alpha_is
    """

    params = []
    conditions = []

    # ID 搜索
    if id_query:
        conditions.append(f"id LIKE {ph}")
        params.append(f"%{id_query}%")

    # 表达式搜索
    if expression_query:
        conditions.append(f"expression LIKE {ph}")
        params.append(f"%{expression_query}%")

    if conditions:
        query_sql += " WHERE " + " AND ".join(conditions)

    # 排序
    if sort_by == 'sharpe':
        query_sql += " ORDER BY sharpe DESC"
    else:
        if DB_TYPE == 'mysql':
            query_sql += " ORDER BY latest_date DESC, sharpe DESC"
        else:
            query_sql += " ORDER BY latest_date DESC NULLS LAST, sharpe DESC"

    query_sql += f" LIMIT {ph}"
    params.append(limit)

    try:
        if DB_TYPE == 'mysql':
            cursor = db.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            data = list(rows)  # 已经是字典列表
        else:
            cursor = db.execute(query_sql, params)
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

        return jsonify({
            "count": len(data),
            "limit": limit,
            "sort": sort_by,
            "data": data
        })
    except Exception as e:
        print(f"Error executing query: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """健康检查接口"""
    return jsonify({
        "status": "running",
        "db_type": DB_TYPE,
        "db_host": DB_HOST if DB_TYPE == 'mysql' else 'local',
        "db_name": DB_NAME if DB_TYPE == 'mysql' else DB_PATH
    })

if __name__ == '__main__':
    print(f"Starting Flask API Server...")
    print(f"DB_TYPE: {DB_TYPE}")
    if DB_TYPE == 'mysql':
        print(f"MySQL: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    else:
        print(f"SQLite: {DB_PATH}")

    app.run(host='0.0.0.0', port=5001, debug=True)
