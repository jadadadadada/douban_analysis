# 爬虫主流程模块
import time
import random
import requests
from spider.parser import (
    parse_top250_list_with_data, parse_movie_detail
)
from spider.user_agents import get_random_ua
import config
import db.dao as dao


class DoubanCrawler:
    """豆瓣电影爬虫"""

    # 豆瓣标签页 API（JSON 接口，更稳定）
    TAG_API_URL = "https://movie.douban.com/j/search_subjects"
    # Top250 URL 模板
    TOP250_URL_TEMPLATE = "https://movie.douban.com/top250?start={start}"

    # 目标标签列表
    TAGS = ['剧情', '喜剧', '爱情', '动作', '科幻', '悬疑', '惊悚', '犯罪', '动画', '纪录片']

    def __init__(self):
        self.session = requests.Session()
        self.min_interval = max(config.CRAWL_MIN_INTERVAL, 3)  # 至少 3 秒
        self.max_interval = max(config.CRAWL_MAX_INTERVAL, 6)  # 至少 6 秒
        self.max_retries = config.CRAWL_MAX_RETRIES
        self.retry_delays = config.CRAWL_RETRY_DELAYS

    def _get_headers(self):
        """获取请求头"""
        return {
            'User-Agent': get_random_ua(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://movie.douban.com/',
            'Connection': 'keep-alive'
        }

    def _random_sleep(self):
        """随机等待一段时间"""
        time.sleep(random.uniform(self.min_interval, self.max_interval))

    def _fetch_page(self, url):
        """请求页面，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                self._random_sleep()
                response = self.session.get(
                    url, headers=self._get_headers(), timeout=15
                )
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    # 被限流，等待更长时间
                    wait_time = self.retry_delays[min(attempt, len(self.retry_delays) - 1)] * 2
                    print(f"被限流(429)，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"请求失败: {url}, 状态码: {response.status_code}")
                    dao.insert_crawl_log(url, response.status_code, 'fail',
                                         f"HTTP {response.status_code}")
            except requests.RequestException as e:
                print(f"请求异常: {url}, 错误: {e}")
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                time.sleep(delay)
                if attempt == self.max_retries - 1:
                    dao.insert_crawl_log(url, 0, 'fail', str(e))
        return None

    def _save_movie(self, movie_data):
        """保存电影数据到数据库"""
        # 检查是否已存在
        if dao.movie_exists(movie_data['douban_id']):
            return False

        # 插入电影
        movie_id = dao.insert_movie(movie_data)
        if not movie_id:
            return False

        # 插入关联数据
        for director_name in movie_data.get('directors', []):
            director_id = dao.insert_director(director_name)
            if director_id:
                dao.link_movie_director(movie_id, director_id)

        for order, actor_name in enumerate(movie_data.get('actors', [])):
            actor_id = dao.insert_actor(actor_name)
            if actor_id:
                dao.link_movie_actor(movie_id, actor_id, order)

        for genre_name in movie_data.get('genres', []):
            genre_id = dao.get_or_create_genre(genre_name)
            if genre_id:
                dao.link_movie_genre(movie_id, genre_id)

        for country_name in movie_data.get('countries', []):
            country_id = dao.get_or_create_country(country_name)
            if country_id:
                dao.link_movie_country(movie_id, country_id)

        for language_name in movie_data.get('languages', []):
            language_id = dao.get_or_create_language(language_name)
            if language_id:
                dao.link_movie_language(movie_id, language_id)

        print(f"保存成功: {movie_data['title']}")
        return True

    def _enrich_movie(self, movie_url):
        """访问详情页获取完整数据（导演、演员、类型等）"""
        detail_html = self._fetch_page(movie_url)
        if detail_html:
            return parse_movie_detail(detail_html, movie_url)
        return None

    def crawl_top250(self):
        """爬取 Top250（10 页 × 25 部）"""
        print("开始爬取 Top250...")
        for page in range(10):
            url = self.TOP250_URL_TEMPLATE.format(start=page * 25)
            print(f"爬取 Top250 第 {page + 1}/10 页: {url}")

            html = self._fetch_page(url)
            if not html:
                continue

            # 从列表页直接提取基础数据
            movies = parse_top250_list_with_data(html)
            print(f"本页找到 {len(movies)} 部电影")

            for movie_data in movies:
                # 先保存基础数据
                if self._save_movie(movie_data):
                    # 新保存的电影，尝试访问详情页补充数据
                    detail_data = self._enrich_movie(movie_data['douban_url'])
                    if detail_data and detail_data.get('genres'):
                        # 更新关联数据
                        movie_id = dao.get_movies(1, 1).get('movies', [{}])[0].get('id')
                        if movie_id:
                            for genre_name in detail_data.get('genres', []):
                                genre_id = dao.get_or_create_genre(genre_name)
                                if genre_id:
                                    dao.link_movie_genre(movie_id, genre_id)

        print("Top250 爬取完成")

    def crawl_by_tag(self, tag):
        """按标签爬取（每个标签前 100 部）"""
        print(f"开始爬取标签: {tag}")
        for start in range(0, 100, 20):  # 每页 20 部，共 5 页
            print(f"爬取标签 {tag} 第 {start // 20 + 1}/5 页")

            # 使用 JSON API
            self._random_sleep()
            try:
                resp = self.session.get(
                    self.TAG_API_URL,
                    params={'type': 'movie', 'tag': tag, 'page_limit': 20, 'page_start': start},
                    headers=self._get_headers(),
                    timeout=15
                )
                if resp.status_code != 200:
                    print(f"标签 API 失败: {resp.status_code}")
                    continue
                data = resp.json()
            except Exception as e:
                print(f"标签 API 异常: {e}")
                continue

            subjects = data.get('subjects', [])
            print(f"本页找到 {len(subjects)} 部电影")

            for item in subjects:
                movie_data = {
                    'douban_id': str(item.get('id', '')),
                    'title': item.get('title', ''),
                    'original_title': '',
                    'year': None,
                    'rating': None,
                    'rating_count': None,
                    'duration_minutes': None,
                    'release_date': None,
                    'summary': '',
                    'poster_url': item.get('cover', ''),
                    'douban_url': item.get('url', ''),
                    'directors': [],
                    'actors': [],
                    'genres': [tag],
                    'countries': [],
                    'languages': []
                }
                # 解析评分
                try:
                    movie_data['rating'] = float(item.get('rate', 0))
                except (ValueError, TypeError):
                    pass

                if movie_data['douban_id']:
                    self._save_movie(movie_data)

        print(f"标签 {tag} 爬取完成")

    def crawl_all(self):
        """主入口：依次爬取 Top250 + 10 个标签"""
        print("=" * 50)
        print("开始豆瓣电影数据爬取")
        print("=" * 50)

        # 爬取 Top250
        self.crawl_top250()

        # 按标签爬取
        for tag in self.TAGS:
            self.crawl_by_tag(tag)

        print("=" * 50)
        print("全部爬取完成")
        print("=" * 50)


if __name__ == '__main__':
    crawler = DoubanCrawler()
    crawler.crawl_all()
