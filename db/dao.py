# 数据访问层 - 封装所有数据库操作
# 所有 SQL 均使用参数化查询，禁止字符串拼接
from db.connection import get_connection, close_connection


# =============================================
# 电影相关操作
# =============================================

def insert_movie(movie_data):
    """插入电影数据，存在则更新，返回电影 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO movies (douban_id, title, original_title, year, rating,
                rating_count, duration_minutes, release_date, summary, poster_url, douban_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title), original_title = VALUES(original_title),
                year = VALUES(year), rating = VALUES(rating),
                rating_count = VALUES(rating_count), duration_minutes = VALUES(duration_minutes),
                release_date = VALUES(release_date), summary = VALUES(summary),
                poster_url = VALUES(poster_url), douban_url = VALUES(douban_url)
        """
        cursor.execute(sql, (
            movie_data['douban_id'], movie_data['title'],
            movie_data.get('original_title'), movie_data.get('year'),
            movie_data.get('rating'), movie_data.get('rating_count'),
            movie_data.get('duration_minutes'), movie_data.get('release_date'),
            movie_data.get('summary'), movie_data.get('poster_url'),
            movie_data.get('douban_url')
        ))
        conn.commit()
        # 获取电影 id
        cursor.execute("SELECT id FROM movies WHERE douban_id = %s", (movie_data['douban_id'],))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        close_connection(conn)


def get_movies(page=1, size=20, genre=None, year=None, min_rating=None, country=None):
    """分页查询电影列表，支持筛选"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # 构建查询条件
        conditions = []
        params = []

        if genre:
            conditions.append("""
                m.id IN (SELECT movie_id FROM movie_genres mg
                         JOIN genres g ON mg.genre_id = g.id WHERE g.name = %s)
            """)
            params.append(genre)
        if year:
            conditions.append("m.year = %s")
            params.append(year)
        if min_rating:
            conditions.append("m.rating >= %s")
            params.append(min_rating)
        if country:
            conditions.append("""
                m.id IN (SELECT movie_id FROM movie_countries mc
                         JOIN countries c ON mc.country_id = c.id WHERE c.name = %s)
            """)
            params.append(country)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 查询总数
        count_sql = "SELECT COUNT(*) as total FROM movies m WHERE " + where_clause
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # 查询分页数据
        offset = (page - 1) * size
        data_sql = (
            "SELECT m.id, m.douban_id, m.title, m.original_title, m.year,"
            " m.rating, m.rating_count, m.duration_minutes,"
            " m.release_date, m.poster_url, m.douban_url"
            " FROM movies m"
            " WHERE " + where_clause +
            " ORDER BY m.rating DESC"
            " LIMIT %s OFFSET %s"
        )
        cursor.execute(data_sql, params + [size, offset])
        movies = cursor.fetchall()

        return {'total': total, 'page': page, 'size': size, 'movies': movies}
    finally:
        close_connection(conn)


def get_movie_by_id(movie_id):
    """获取电影详情（含导演、演员、类型、国家、语言）"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 查询电影基本信息
        cursor.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
        movie = cursor.fetchone()
        if not movie:
            return None

        # 查询导演
        cursor.execute("""
            SELECT d.name FROM directors d
            JOIN movie_directors md ON d.id = md.director_id
            WHERE md.movie_id = %s
        """, (movie_id,))
        movie['directors'] = [row['name'] for row in cursor.fetchall()]

        # 查询演员
        cursor.execute("""
            SELECT a.name FROM actors a
            JOIN movie_actors ma ON a.id = ma.actor_id
            WHERE ma.movie_id = %s
            ORDER BY ma.order_no
        """, (movie_id,))
        movie['actors'] = [row['name'] for row in cursor.fetchall()]

        # 查询类型
        cursor.execute("""
            SELECT g.name FROM genres g
            JOIN movie_genres mg ON g.id = mg.genre_id
            WHERE mg.movie_id = %s
        """, (movie_id,))
        movie['genres'] = [row['name'] for row in cursor.fetchall()]

        # 查询国家
        cursor.execute("""
            SELECT c.name FROM countries c
            JOIN movie_countries mc ON c.id = mc.country_id
            WHERE mc.movie_id = %s
        """, (movie_id,))
        movie['countries'] = [row['name'] for row in cursor.fetchall()]

        # 查询语言
        cursor.execute("""
            SELECT l.name FROM languages l
            JOIN movie_languages ml ON l.id = ml.language_id
            WHERE ml.movie_id = %s
        """, (movie_id,))
        movie['languages'] = [row['name'] for row in cursor.fetchall()]

        return movie
    finally:
        close_connection(conn)


def search_movies(keyword):
    """关键词搜索电影"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT id, douban_id, title, original_title, year, rating,
                   rating_count, poster_url
            FROM movies
            WHERE title LIKE %s OR original_title LIKE %s
            ORDER BY rating DESC
            LIMIT 50
        """
        like_keyword = f"%{keyword}%"
        cursor.execute(sql, (like_keyword, like_keyword))
        return cursor.fetchall()
    finally:
        close_connection(conn)


def movie_exists(douban_id):
    """检查电影是否已存在"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies WHERE douban_id = %s", (douban_id,))
        return cursor.fetchone()[0] > 0
    finally:
        close_connection(conn)


# =============================================
# 关联数据操作
# =============================================

def insert_director(name, douban_id=None):
    """插入导演，返回 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO directors (name, douban_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name)
        """
        cursor.execute(sql, (name, douban_id))
        conn.commit()
        # 获取导演 id
        if douban_id:
            cursor.execute("SELECT id FROM directors WHERE douban_id = %s", (douban_id,))
        else:
            cursor.execute("SELECT id FROM directors WHERE name = %s AND douban_id IS NULL", (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        close_connection(conn)


def insert_actor(name, douban_id=None):
    """插入演员，返回 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO actors (name, douban_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name)
        """
        cursor.execute(sql, (name, douban_id))
        conn.commit()
        if douban_id:
            cursor.execute("SELECT id FROM actors WHERE douban_id = %s", (douban_id,))
        else:
            cursor.execute("SELECT id FROM actors WHERE name = %s AND douban_id IS NULL", (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        close_connection(conn)


def get_or_create_genre(name):
    """获取或创建类型，返回 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM genres WHERE name = %s", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("INSERT INTO genres (name) VALUES (%s)", (name,))
        conn.commit()
        return cursor.lastrowid
    finally:
        close_connection(conn)


def get_or_create_country(name):
    """获取或创建国家，返回 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM countries WHERE name = %s", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("INSERT INTO countries (name) VALUES (%s)", (name,))
        conn.commit()
        return cursor.lastrowid
    finally:
        close_connection(conn)


def get_or_create_language(name):
    """获取或创建语言，返回 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE name = %s", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("INSERT INTO languages (name) VALUES (%s)", (name,))
        conn.commit()
        return cursor.lastrowid
    finally:
        close_connection(conn)


def link_movie_director(movie_id, director_id):
    """关联电影和导演"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT IGNORE INTO movie_directors (movie_id, director_id)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (movie_id, director_id))
        conn.commit()
    finally:
        close_connection(conn)


def link_movie_actor(movie_id, actor_id, order_no=0):
    """关联电影和演员"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO movie_actors (movie_id, actor_id, order_no)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE order_no = VALUES(order_no)
        """
        cursor.execute(sql, (movie_id, actor_id, order_no))
        conn.commit()
    finally:
        close_connection(conn)


def link_movie_genre(movie_id, genre_id):
    """关联电影和类型"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT IGNORE INTO movie_genres (movie_id, genre_id)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (movie_id, genre_id))
        conn.commit()
    finally:
        close_connection(conn)


def link_movie_country(movie_id, country_id):
    """关联电影和国家"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT IGNORE INTO movie_countries (movie_id, country_id)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (movie_id, country_id))
        conn.commit()
    finally:
        close_connection(conn)


def link_movie_language(movie_id, language_id):
    """关联电影和语言"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT IGNORE INTO movie_languages (movie_id, language_id)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (movie_id, language_id))
        conn.commit()
    finally:
        close_connection(conn)


# =============================================
# 统计查询
# =============================================


def _build_filter_conditions(genre=None, year=None, country=None, min_rating=None, table_alias='m'):
    """构建筛选条件子句和参数，支持自定义表别名"""
    conditions = []
    params = []
    if genre:
        conditions.append(
            f"{table_alias}.id IN (SELECT movie_id FROM movie_genres mg "
            "JOIN genres g ON mg.genre_id = g.id WHERE g.name = %s)"
        )
        params.append(genre)
    if year:
        conditions.append(f"{table_alias}.year = %s")
        params.append(int(year))
    if country:
        conditions.append(
            f"{table_alias}.id IN (SELECT movie_id FROM movie_countries mc "
            "JOIN countries c ON mc.country_id = c.id WHERE c.name = %s)"
        )
        params.append(country)
    if min_rating and float(min_rating) > 0:
        conditions.append(f"{table_alias}.rating >= %s")
        params.append(float(min_rating))
    return conditions, params


def get_genre_distribution(genre=None, year=None, country=None, min_rating=None):
    """各类型电影数量"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
            sql = f"""
                SELECT g.name, COUNT(mg.movie_id) as count
                FROM genres g
                JOIN movie_genres mg ON g.id = mg.genre_id
                JOIN movies m ON mg.movie_id = m.id
                {where}
                GROUP BY g.id, g.name
                ORDER BY count DESC
            """
        else:
            sql = """
                SELECT g.name, COUNT(mg.movie_id) as count
                FROM genres g
                JOIN movie_genres mg ON g.id = mg.genre_id
                GROUP BY g.id, g.name
                ORDER BY count DESC
            """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_rating_distribution(genre=None, year=None, country=None, min_rating=None):
    """评分区间分布"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.rating IS NOT NULL")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
            SELECT
                CASE
                    WHEN rating >= 0 AND rating < 5 THEN '0-5分'
                    WHEN rating >= 5 AND rating < 6 THEN '5-6分'
                    WHEN rating >= 6 AND rating < 7 THEN '6-7分'
                    WHEN rating >= 7 AND rating < 8 THEN '7-8分'
                    WHEN rating >= 8 AND rating < 9 THEN '8-9分'
                    WHEN rating >= 9 AND rating <= 10 THEN '9-10分'
                END as range_label,
                COUNT(*) as count
            FROM movies m
            {where}
            GROUP BY range_label
            ORDER BY MIN(m.rating)
        """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_year_trend(genre=None, year=None, country=None, min_rating=None):
    """年代电影数量与均分趋势"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.year IS NOT NULL AND m.year >= 1970")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
            SELECT m.year, COUNT(*) as count, ROUND(AVG(m.rating), 1) as avg_rating
            FROM movies m
            {where}
            GROUP BY m.year
            ORDER BY m.year
        """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_country_distribution(genre=None, year=None, country=None, min_rating=None):
    """各国/地区电影数量"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
            sql = f"""
                SELECT c.name, COUNT(mc.movie_id) as count
                FROM countries c
                JOIN movie_countries mc ON c.id = mc.country_id
                JOIN movies m ON mc.movie_id = m.id
                {where}
                GROUP BY c.id, c.name
                ORDER BY count DESC
                LIMIT 30
            """
        else:
            sql = """
                SELECT c.name, COUNT(mc.movie_id) as count
                FROM countries c
                JOIN movie_countries mc ON c.id = mc.country_id
                GROUP BY c.id, c.name
                ORDER BY count DESC
                LIMIT 30
            """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_top_rated(limit=20, genre=None, year=None, country=None, min_rating=None):
    """评分最高的电影"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.rating IS NOT NULL")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
            SELECT m.id, m.title, m.year, m.rating, m.rating_count, m.poster_url
            FROM movies m
            {where}
            ORDER BY m.rating DESC
            LIMIT %s
        """
        cursor.execute(sql, params + [limit])
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_genre_year_heatmap(genre=None, year=None, country=None, min_rating=None):
    """年份×类型矩阵数据"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.year IS NOT NULL AND m.year >= 1980")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
            SELECT m.year, g.name as genre, COUNT(*) as count
            FROM movies m
            JOIN movie_genres mg ON m.id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.id
            {where}
            GROUP BY m.year, g.name
            ORDER BY m.year, g.name
        """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_director_network(genre=None, year=None, country=None, min_rating=None):
    """导演-演员协作关系"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # 使用独立别名避免子查询冲突
        conditions, params = _build_filter_conditions(genre, year, country, min_rating, table_alias='m2')
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
            movie_filter = f"AND md.movie_id IN (SELECT m2.id FROM movies m2 {where})"
        else:
            movie_filter = ""
        sql = f"""
            SELECT d.name as director, a.name as actor, COUNT(*) as count
            FROM movie_directors md
            JOIN movie_actors ma ON md.movie_id = ma.movie_id
            JOIN directors d ON md.director_id = d.id
            JOIN actors a ON ma.actor_id = a.id
            WHERE 1=1 {movie_filter}
            GROUP BY d.id, d.name, a.id, a.name
            HAVING count >= 2
            ORDER BY count DESC
            LIMIT 100
        """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_all_summaries(genre=None, year=None, country=None, min_rating=None):
    """获取所有电影简介（供分词）"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.summary IS NOT NULL AND m.summary != ''")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"SELECT m.summary FROM movies m {where}"
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_duration_rating_data(genre=None, year=None, country=None, min_rating=None):
    """时长与评分数据"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        conditions.append("m.duration_minutes IS NOT NULL AND m.rating IS NOT NULL AND m.duration_minutes > 0 AND m.duration_minutes < 300")
        where = "WHERE " + " AND ".join(conditions)
        sql = f"""
            SELECT m.duration_minutes, m.rating
            FROM movies m
            {where}
        """
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_summary_stats(genre=None, year=None, country=None, min_rating=None):
    """核心指标统计"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions, params = _build_filter_conditions(genre, year, country, min_rating)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        result = {}
        cursor.execute(f"SELECT COUNT(*) as total FROM movies m {where}", params)
        result['total_movies'] = cursor.fetchone()['total']

        rating_conditions = conditions + ["m.rating IS NOT NULL"] if conditions else ["m.rating IS NOT NULL"]
        rating_where = "WHERE " + " AND ".join(rating_conditions)
        cursor.execute(f"SELECT ROUND(AVG(m.rating), 1) as avg FROM movies m {rating_where}", params)
        result['avg_rating'] = cursor.fetchone()['avg'] or 0

        director_sql = f"""
            SELECT COUNT(DISTINCT md.director_id) as total
            FROM movie_directors md
            JOIN movies m ON md.movie_id = m.id
            {where}
        """
        cursor.execute(director_sql, params)
        result['total_directors'] = cursor.fetchone()['total']

        actor_sql = f"""
            SELECT COUNT(DISTINCT ma.actor_id) as total
            FROM movie_actors ma
            JOIN movies m ON ma.movie_id = m.id
            {where}
        """
        cursor.execute(actor_sql, params)
        result['total_actors'] = cursor.fetchone()['total']

        return result
    finally:
        close_connection(conn)


# =============================================
# 筛选选项
# =============================================

def get_all_genres():
    """获取所有类型"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM genres ORDER BY name")
        return [row['name'] for row in cursor.fetchall()]
    finally:
        close_connection(conn)


def get_all_years():
    """获取所有年份"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT year FROM movies WHERE year IS NOT NULL ORDER BY year DESC")
        return [row['year'] for row in cursor.fetchall()]
    finally:
        close_connection(conn)


def get_all_countries():
    """获取所有国家"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM countries ORDER BY name")
        return [row['name'] for row in cursor.fetchall()]
    finally:
        close_connection(conn)


# =============================================
# 爬虫日志
# =============================================

def insert_crawl_log(url, status_code, status, error_msg=None):
    """插入爬虫日志"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO crawl_logs (url, status_code, status, error_msg)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (url, status_code, status, error_msg))
        conn.commit()
    finally:
        close_connection(conn)


# =============================================
# 用户系统
# =============================================

def insert_user(username, password_hash, email=None):
    """注册用户，返回用户 id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, password_hash, email))
        conn.commit()
        return cursor.lastrowid
    finally:
        close_connection(conn)


def get_user_by_username(username):
    """根据用户名查询用户"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    finally:
        close_connection(conn)


def get_user_by_id(user_id):
    """根据 ID 查询用户"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        close_connection(conn)


def add_favorite(user_id, movie_id):
    """收藏电影"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "INSERT IGNORE INTO user_favorites (user_id, movie_id) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, movie_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        close_connection(conn)


def remove_favorite(user_id, movie_id):
    """取消收藏"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM user_favorites WHERE user_id = %s AND movie_id = %s"
        cursor.execute(sql, (user_id, movie_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        close_connection(conn)


def is_favorited(user_id, movie_id):
    """检查是否已收藏"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM user_favorites WHERE user_id = %s AND movie_id = %s"
        cursor.execute(sql, (user_id, movie_id))
        return cursor.fetchone()[0] > 0
    finally:
        close_connection(conn)


def get_user_favorites(user_id, page=1, size=20):
    """获取用户收藏列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        offset = (page - 1) * size
        sql = """
            SELECT m.id, m.title, m.year, m.rating, m.poster_url, uf.created_at as favorited_at
            FROM user_favorites uf
            JOIN movies m ON uf.movie_id = m.id
            WHERE uf.user_id = %s
            ORDER BY uf.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (user_id, size, offset))
        movies = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total FROM user_favorites WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()['total']

        return {'total': total, 'page': page, 'size': size, 'movies': movies}
    finally:
        close_connection(conn)


def add_or_update_rating(user_id, movie_id, rating):
    """添加或更新用户评分"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO user_ratings (user_id, movie_id, rating)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE rating = VALUES(rating)
        """
        cursor.execute(sql, (user_id, movie_id, rating))
        conn.commit()
    finally:
        close_connection(conn)


def remove_rating(user_id, movie_id):
    """删除用户评分"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM user_ratings WHERE user_id = %s AND movie_id = %s"
        cursor.execute(sql, (user_id, movie_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        close_connection(conn)


def get_user_rating(user_id, movie_id):
    """查询用户对某部电影的评分"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT rating FROM user_ratings WHERE user_id = %s AND movie_id = %s"
        cursor.execute(sql, (user_id, movie_id))
        row = cursor.fetchone()
        return float(row['rating']) if row else None
    finally:
        close_connection(conn)


def get_movie_user_ratings(movie_id):
    """获取电影的用户评分列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT ur.rating, ur.created_at, u.username
            FROM user_ratings ur
            JOIN users u ON ur.user_id = u.id
            WHERE ur.movie_id = %s
            ORDER BY ur.created_at DESC
        """
        cursor.execute(sql, (movie_id,))
        return cursor.fetchall()
    finally:
        close_connection(conn)


def get_user_ratings_list(user_id, page=1, size=20):
    """获取用户评分列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        offset = (page - 1) * size
        sql = """
            SELECT m.id, m.title, m.year, m.rating, m.rating as douban_rating, m.poster_url,
                   ur.rating as user_rating, ur.created_at as rated_at
            FROM user_ratings ur
            JOIN movies m ON ur.movie_id = m.id
            WHERE ur.user_id = %s
            ORDER BY ur.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (user_id, size, offset))
        movies = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total FROM user_ratings WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()['total']

        return {'total': total, 'page': page, 'size': size, 'movies': movies}
    finally:
        close_connection(conn)
