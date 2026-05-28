# 数据库连接管理模块
import mysql.connector
from mysql.connector import Error
import config


def get_connection():
    """获取数据库连接"""
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset=config.DB_CHARSET
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"数据库连接失败: {e}")
        raise


def close_connection(conn):
    """关闭数据库连接"""
    if conn and conn.is_connected():
        conn.close()
