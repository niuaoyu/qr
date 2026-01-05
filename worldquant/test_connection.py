"""
测试数据库连接和多机协作环境
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config import DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_NAME, USER_CHOICE


def test_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("环境检测")
    print("=" * 50)
    print(f"USER_CHOICE: {os.getenv('USER_CHOICE', '未设置')}")
    print(f"DB_TYPE: {DB_TYPE}")
    print(f"DB_HOST: {DB_HOST}")
    print(f"DB_PORT: {DB_PORT}")
    print(f"DB_USER: {DB_USER}")
    print(f"DB_NAME: {DB_NAME}")
    print()

    # 测试数据库连接
    print("=" * 50)
    print("测试数据库连接")
    print("=" * 50)
    try:
        from storage.database import get_connection, init_db
        conn = get_connection()
        print("✅ 数据库连接成功")

        # 初始化表
        conn = init_db()
        print("✅ 数据库表初始化成功")

        # 查询记录数
        cursor = conn.cursor()
        if DB_TYPE == 'mysql':
            cursor.execute("SELECT COUNT(*) as cnt FROM alpha_is")
            result = cursor.fetchone()
            count = result['cnt']
        else:
            cursor.execute("SELECT COUNT(*) FROM alpha_is")
            count = cursor.fetchone()[0]

        print(f"✅ alpha_is 表记录数: {count}")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_fingerprint():
    """测试指纹功能"""
    print()
    print("=" * 50)
    print("测试指纹去重")
    print("=" * 50)
    try:
        from core.fingerprint import generate_fingerprint
        from storage.database import get_connection, check_exists

        test_expr = "group_rank(ts_rank(sales/assets, 252), industry)"
        test_settings = {"region": "USA", "universe": "TOP3000", "delay": 1}

        fp = generate_fingerprint(test_expr, test_settings)
        print(f"测试表达式: {test_expr[:40]}...")
        print(f"生成指纹: {fp}")

        conn = get_connection()
        exists = check_exists(conn, fp)
        print(f"数据库中是否存在: {'是' if exists else '否'}")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 指纹测试失败: {e}")
        return False


if __name__ == "__main__":
    ok1 = test_connection()
    ok2 = test_fingerprint()

    print()
    print("=" * 50)
    if ok1 and ok2:
        print("✅ 所有测试通过，环境配置正确！")
    else:
        print("❌ 部分测试失败，请检查配置")
    print("=" * 50)
