# 补充电影详情数据脚本（使用豆瓣移动端 API）
# 用法：在项目根目录执行 python scripts/enrich_details.py
# 策略：跳过已有数据的电影，遇到 400 自动等待重试，429 立即停止
import os
import sys
import time
import random
import re
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.connection import get_connection, close_connection

# 移动端 API
MOBILE_API = "https://m.douban.com/rexxar/api/v2/movie/{douban_id}"

# 基础间隔（秒）
BASE_INTERVAL = 8
# 遇到 400 后的等待时间
RATE_LIMIT_WAIT = 30


def get_headers(douban_id):
    return {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': f'https://m.douban.com/movie/subject/{douban_id}',
        'Origin': 'https://m.douban.com',
    }


def get_movies_to_enrich():
    """查询需要补充数据的电影（跳过已有演员数据的）"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id, m.douban_id, m.douban_url, m.title
            FROM movies m
            WHERE m.id NOT IN (
                SELECT DISTINCT movie_id FROM movie_actors
            )
            ORDER BY m.id
        """)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def update_movie_detail(movie_id, data):
    """用 API 数据更新电影详情（单连接 + buffered cursor）"""
    duration = None
    durations = data.get('durations', [])
    if durations:
        m = re.search(r'(\d+)', str(durations[0]))
        if m:
            duration = int(m.group(1))

    summary = data.get('intro', '') or ''

    release_date = None
    pubdates = data.get('pubdate', [])
    if pubdates:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', str(pubdates[0]))
        if m:
            release_date = m.group(1)

    actors = [a.get('name', '') for a in data.get('actors', []) if a.get('name')]
    countries = [c for c in data.get('countries', []) if c]
    languages = [l for l in data.get('languages', []) if l]

    conn = get_connection()
    try:
        cursor = conn.cursor(buffered=True)

        cursor.execute("""
            UPDATE movies SET
                duration_minutes = COALESCE(duration_minutes, %s),
                summary = CASE WHEN summary IS NULL OR summary = '' THEN %s ELSE summary END,
                release_date = COALESCE(release_date, %s)
            WHERE id = %s
        """, (duration, summary or None, release_date, movie_id))
        conn.commit()

        for order, name in enumerate(actors):
            cursor.execute(
                "INSERT INTO actors (name) VALUES (%s) ON DUPLICATE KEY UPDATE name = VALUES(name)",
                (name,)
            )
            cursor.execute("SELECT id FROM actors WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "INSERT INTO movie_actors (movie_id, actor_id, order_no) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE order_no = VALUES(order_no)",
                    (movie_id, row[0], order)
                )

        for name in countries:
            cursor.execute(
                "INSERT INTO countries (name) VALUES (%s) ON DUPLICATE KEY UPDATE name = VALUES(name)",
                (name,)
            )
            cursor.execute("SELECT id FROM countries WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "INSERT IGNORE INTO movie_countries (movie_id, country_id) VALUES (%s, %s)",
                    (movie_id, row[0])
                )

        for name in languages:
            cursor.execute(
                "INSERT INTO languages (name) VALUES (%s) ON DUPLICATE KEY UPDATE name = VALUES(name)",
                (name,)
            )
            cursor.execute("SELECT id FROM languages WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "INSERT IGNORE INTO movie_languages (movie_id, language_id) VALUES (%s, %s)",
                    (movie_id, row[0])
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        close_connection(conn)


def main():
    movies = get_movies_to_enrich()
    print(f"需补充详情的电影: {len(movies)} 部")
    print(f"基础间隔: {BASE_INTERVAL}s, 限流等待: {RATE_LIMIT_WAIT}s")
    print("=" * 50)

    session = requests.Session()
    success_count = 0
    fail_count = 0
    consecutive_fails = 0  # 连续失败计数

    for i, movie in enumerate(movies):
        douban_id = movie['douban_id']
        title = movie['title']
        print(f"[{i + 1}/{len(movies)}] {title} (ID: {douban_id})", end='', flush=True)

        # 动态间隔：连续失败越多，等得越久
        interval = BASE_INTERVAL + consecutive_fails * 5
        time.sleep(interval)

        url = MOBILE_API.format(douban_id=douban_id)
        try:
            resp = session.get(url, headers=get_headers(douban_id), timeout=15)

            if resp.status_code == 429:
                print(f" -> 429 限流！停止！")
                break

            if resp.status_code == 400:
                # 被限流，等待后重试一次
                print(f" -> 400, 等待 {RATE_LIMIT_WAIT}s 重试...", end='', flush=True)
                time.sleep(RATE_LIMIT_WAIT)
                resp = session.get(url, headers=get_headers(douban_id), timeout=15)
                if resp.status_code == 400:
                    print(f" 仍 400, 跳过")
                    fail_count += 1
                    consecutive_fails += 1
                    continue
                elif resp.status_code == 429:
                    print(f" 429 限流！停止！")
                    break

            if resp.status_code != 200:
                print(f" -> HTTP {resp.status_code}")
                fail_count += 1
                consecutive_fails += 1
                continue

            data = resp.json()
            update_movie_detail(movie['id'], data)

            actors = [a.get('name') for a in data.get('actors', [])]
            countries = data.get('countries', [])
            durations = data.get('durations', [])
            has_summary = bool(data.get('intro'))
            print(f" -> OK 演员:{len(actors)} 国家:{len(countries)} 时长:{durations} 简介:{has_summary}")
            success_count += 1
            consecutive_fails = 0  # 成功后重置

        except requests.RequestException as e:
            print(f" -> 异常: {e}")
            fail_count += 1
            consecutive_fails += 1
        except Exception as e:
            print(f" -> 解析异常: {e}")
            fail_count += 1
            consecutive_fails += 1

    print(f"\n{'=' * 50}")
    print(f"成功: {success_count}  失败: {fail_count}  总计: {len(movies)}")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    main()
