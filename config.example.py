# 数据库配置示例
# 使用方法：复制本文件为 config.py，然后填写本机 MySQL 密码。
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'douban_movies'
DB_USER = 'root'
DB_PASSWORD = ''
DB_CHARSET = 'utf8mb4'

# 爬虫配置
CRAWL_MIN_INTERVAL = 1
CRAWL_MAX_INTERVAL = 3
CRAWL_MAX_RETRIES = 3
CRAWL_RETRY_DELAYS = [2, 4, 8]

# Flask 配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = 'change-this-secret-key'
