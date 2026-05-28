"""项目运行体检脚本。

运行方式：
    python health_check.py
"""
import importlib
import sys


REQUIRED_MODULES = [
    ('flask', 'Flask'),
    ('mysql.connector', 'mysql-connector-python'),
    ('requests', 'requests'),
    ('bs4', 'beautifulsoup4'),
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('jieba', 'jieba'),
]


def check_python_version():
    """检查 Python 版本。"""
    version = sys.version_info
    ok = version.major == 3 and version.minor >= 10
    print(f"[{'OK' if ok else 'FAIL'}] Python 版本: {sys.version.split()[0]}")
    return ok


def check_modules():
    """检查第三方依赖。"""
    ok = True
    for module_name, package_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"[OK] 依赖已安装: {package_name}")
        except ImportError:
            print(f"[FAIL] 缺少依赖: {package_name}")
            ok = False
    return ok


def check_flask_app():
    """检查 Flask 应用是否能创建。"""
    try:
        from app import create_app

        app = create_app()
        print(f"[OK] Flask 应用创建成功，路由数量: {len(app.url_map._rules)}")
        return True
    except Exception as exc:
        print(f"[FAIL] Flask 应用创建失败: {exc}")
        return False


def check_database():
    """检查数据库连接。"""
    try:
        from db.connection import close_connection, get_connection

        conn = get_connection()
        print("[OK] MySQL 数据库连接成功")
        close_connection(conn)
        return True
    except Exception as exc:
        print(f"[FAIL] MySQL 数据库连接失败: {exc}")
        return False


def main():
    """执行体检。"""
    print("豆瓣电影数据分析系统 - 运行体检")
    print("=" * 40)
    checks = [
        check_python_version(),
        check_modules(),
        check_flask_app(),
        check_database(),
    ]
    print("=" * 40)
    if all(checks):
        print("体检通过，可以启动服务：python app.py")
    else:
        print("体检未通过，请先根据 FAIL 项修复环境或配置。")


if __name__ == '__main__':
    main()
