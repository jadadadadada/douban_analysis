# 海报下载脚本 — 将豆瓣海报图片保存到本地
# 用法：在项目根目录执行 python scripts/download_posters.py
import os
import sys
import time
import random
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests as http_requests
import mysql.connector
import config

POSTER_DIR = os.path.join(PROJECT_ROOT, 'static', 'posters')
os.makedirs(POSTER_DIR, exist_ok=True)

HEADERS = {
    'Referer': 'https://movie.douban.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def download_posters():
    conn = mysql.connector.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, charset=config.DB_CHARSET
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, douban_id, title, poster_url FROM movies WHERE poster_url IS NOT NULL AND poster_url != "" ORDER BY id')
    movies = cursor.fetchall()

    success = 0
    skip = 0
    fail = 0

    for i, m in enumerate(movies):
        local_filename = f'{m["douban_id"]}.jpg'
        local_path = os.path.join(POSTER_DIR, local_filename)
        web_path = f'/static/posters/{local_filename}'

        # 已下载则跳过
        if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
            skip += 1
            # 更新数据库中的海报路径为本地路径
            cursor.execute('UPDATE movies SET poster_url = %s WHERE id = %s', (web_path, m['id']))
            continue

        # 带重试的下载
        downloaded = False
        for retry in range(3):
            try:
                resp = http_requests.get(m['poster_url'], headers=HEADERS, timeout=10, verify=False)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    with open(local_path, 'wb') as f:
                        f.write(resp.content)
                    cursor.execute('UPDATE movies SET poster_url = %s WHERE id = %s', (web_path, m['id']))
                    success += 1
                    downloaded = True
                    print(f'  [{i+1}/{len(movies)}] {m["title"]}: OK ({len(resp.content)} bytes)')
                    break
                elif resp.status_code == 200:
                    # 占位小图，跳过
                    print(f'  [{i+1}/{len(movies)}] {m["title"]}: 占位图 ({len(resp.content)}B)，跳过')
                    downloaded = True
                    break
                else:
                    print(f'  [{i+1}/{len(movies)}] {m["title"]}: HTTP {resp.status_code}，重试...')
            except Exception as e:
                print(f'  [{i+1}/{len(movies)}] {m["title"]}: 连接失败，重试...')

            # 指数退避
            wait = (retry + 1) * 5 + random.uniform(1, 3)
            print(f'    等待 {wait:.1f}s...')
            time.sleep(wait)

        if not downloaded:
            fail += 1
            print(f'  [{i+1}/{len(movies)}] {m["title"]}: 下载失败')

        # 每次请求间隔 2-3 秒，避免触发限流
        time.sleep(random.uniform(2, 3))

    conn.commit()
    conn.close()

    print(f'\n完成！成功: {success}, 跳过(已有): {skip}, 失败: {fail}, 总计: {len(movies)}')


if __name__ == '__main__':
    print('开始下载海报图片...')
    print(f'保存目录: {POSTER_DIR}')
    print()
    download_posters()
