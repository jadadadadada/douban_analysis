# HTML 解析模块 - 使用 BeautifulSoup4 解析豆瓣电影页面
import re
from bs4 import BeautifulSoup


def parse_top250_list(html):
    """解析 Top250 列表页，返回电影详情页链接列表"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    # Top250 列表页中每个电影项的链接
    for item in soup.select('.grid_view .item a[href*="subject"]'):
        href = item.get('href', '')
        if href and 'subject' in href and href not in links:
            links.append(href)
    return links


def parse_top250_list_with_data(html):
    """解析 Top250 列表页，直接提取基础数据（减少详情页请求）"""
    soup = BeautifulSoup(html, 'lxml')
    movies = []
    for item in soup.select('.grid_view .item'):
        movie = {
            'douban_id': '',
            'title': '',
            'original_title': '',
            'year': None,
            'rating': None,
            'rating_count': None,
            'duration_minutes': None,
            'release_date': None,
            'summary': '',
            'poster_url': '',
            'douban_url': '',
            'directors': [],
            'actors': [],
            'genres': [],
            'countries': [],
            'languages': []
        }
        # 链接和 ID
        link_tag = item.select_one('a[href*="subject"]')
        if link_tag:
            href = link_tag.get('href', '')
            movie['douban_url'] = href
            id_match = re.search(r'/subject/(\d+)', href)
            if id_match:
                movie['douban_id'] = id_match.group(1)

        # 标题
        title_tag = item.select_one('.title')
        if title_tag:
            movie['title'] = title_tag.get_text(strip=True)

        # 评分
        rating_tag = item.select_one('.rating_num')
        if rating_tag:
            try:
                movie['rating'] = float(rating_tag.get_text(strip=True))
            except (ValueError, TypeError):
                pass

        # 评分人数
        people_tag = item.select_one('.star span:last-child')
        if people_tag:
            text = people_tag.get_text(strip=True)
            num_match = re.search(r'(\d+)', text)
            if num_match:
                movie['rating_count'] = int(num_match.group(1))

        # 年份、导演、演员（从 bd > p 第一行提取）
        info_tag = item.select_one('.bd p')
        if info_tag:
            info_text = info_tag.get_text()
            # 年份
            year_match = re.search(r'(\d{4})', info_text)
            if year_match:
                movie['year'] = int(year_match.group(1))
            # 导演
            director_match = re.search(r'导演:\s*(.+?)(?:\s{3}|主演:|$)', info_text)
            if director_match:
                directors_text = director_match.group(1)
                movie['directors'] = [d.strip() for d in directors_text.split('/') if d.strip()]

        # 海报
        img_tag = item.select_one('img')
        if img_tag:
            movie['poster_url'] = img_tag.get('src', '')

        if movie['douban_id']:
            movies.append(movie)
    return movies


def parse_tag_list(html):
    """解析标签页列表，返回电影详情页链接列表"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    # 标签页中电影链接
    for item in soup.select('.article .item a[href*="subject"]'):
        href = item.get('href', '')
        if href and 'subject' in href and href not in links:
            links.append(href)
    return links


def parse_tag_list_with_data(html, default_genres=None):
    """解析标签页列表，直接提取基础数据"""
    soup = BeautifulSoup(html, 'lxml')
    movies = []
    for item in soup.select('.article .item'):
        movie = {
            'douban_id': '',
            'title': '',
            'original_title': '',
            'year': None,
            'rating': None,
            'rating_count': None,
            'duration_minutes': None,
            'release_date': None,
            'summary': '',
            'poster_url': '',
            'douban_url': '',
            'directors': [],
            'actors': [],
            'genres': list(default_genres) if default_genres else [],
            'countries': [],
            'languages': []
        }
        # 链接和 ID
        link_tag = item.select_one('a[href*="subject"]')
        if link_tag:
            href = link_tag.get('href', '')
            movie['douban_url'] = href
            id_match = re.search(r'/subject/(\d+)', href)
            if id_match:
                movie['douban_id'] = id_match.group(1)

        # 标题
        title_tag = item.select_one('.title') or item.select_one('a')
        if title_tag:
            movie['title'] = title_tag.get_text(strip=True)

        # 评分
        rating_tag = item.select_one('.rating_nums') or item.select_one('.rating_num')
        if rating_tag:
            try:
                movie['rating'] = float(rating_tag.get_text(strip=True))
            except (ValueError, TypeError):
                pass

        # 评分人数
        people_tag = item.select_one('.pl')
        if people_tag:
            text = people_tag.get_text(strip=True)
            num_match = re.search(r'(\d+)', text)
            if num_match:
                movie['rating_count'] = int(num_match.group(1))

        if movie['douban_id']:
            movies.append(movie)
    return movies


def parse_movie_detail(html, url=''):
    """解析电影详情页，返回结构化数据字典"""
    soup = BeautifulSoup(html, 'lxml')
    data = {
        'douban_id': '',
        'title': '',
        'original_title': '',
        'year': None,
        'rating': None,
        'rating_count': None,
        'duration_minutes': None,
        'release_date': None,
        'summary': '',
        'poster_url': '',
        'douban_url': url,
        'directors': [],
        'actors': [],
        'genres': [],
        'countries': [],
        'languages': []
    }

    # 从 URL 提取 douban_id
    match = re.search(r'/subject/(\d+)', url)
    if match:
        data['douban_id'] = match.group(1)

    # 标题
    title_tag = soup.select_one('h1 span')
    if title_tag:
        data['title'] = title_tag.get_text(strip=True)

    # 原名
    original_title_tag = soup.select_one('h1 .year') or soup.select_one('span.year')
    if not original_title_tag:
        # 尝试从页面信息中获取
        info_div = soup.select_one('#info')
        if info_div:
            text = info_div.get_text()
            match = re.search(r'原名:\s*(.+?)(?:\n|$)', text)
            if match:
                data['original_title'] = match.group(1).strip()

    # 年份
    year_tag = soup.select_one('h1 .year')
    if year_tag:
        year_match = re.search(r'(\d{4})', year_tag.get_text())
        if year_match:
            data['year'] = int(year_match.group(1))

    # 评分
    rating_tag = soup.select_one('.rating_num')
    if rating_tag:
        try:
            data['rating'] = float(rating_tag.get_text(strip=True))
        except (ValueError, TypeError):
            pass

    # 评分人数
    rating_count_tag = soup.select_one('.rating_people span')
    if rating_count_tag:
        try:
            data['rating_count'] = int(rating_count_tag.get_text(strip=True))
        except (ValueError, TypeError):
            pass

    # 信息区域解析
    info_div = soup.select_one('#info')
    if info_div:
        info_text = info_div.get_text()

        # 导演
        director_links = info_div.select('a[rel="v:directedBy"]')
        data['directors'] = [a.get_text(strip=True) for a in director_links]

        # 演员
        actor_links = info_div.select('a[rel="v:starring"]')
        data['actors'] = [a.get_text(strip=True) for a in actor_links]

        # 类型
        genre_spans = info_div.select('span[property="v:genre"]')
        data['genres'] = [s.get_text(strip=True) for s in genre_spans]

        # 国家/地区
        country_match = re.search(r'制片国家/地区:\s*(.+?)(?:\n|$)', info_text)
        if country_match:
            data['countries'] = [c.strip() for c in country_match.group(1).split('/')]

        # 语言
        language_match = re.search(r'语言:\s*(.+?)(?:\n|$)', info_text)
        if language_match:
            data['languages'] = [l.strip() for l in language_match.group(1).split('/')]

        # 片长
        duration_tag = info_div.select_one('span[property="v:runtime"]')
        if duration_tag:
            try:
                data['duration_minutes'] = int(re.search(r'\d+', duration_tag.get_text()).group())
            except (ValueError, TypeError, AttributeError):
                pass

        # 上映日期
        release_tags = info_div.select('span[property="v:initialReleaseDate"]')
        if release_tags:
            date_text = release_tags[0].get_text(strip=True)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
            if date_match:
                data['release_date'] = date_match.group(1)

    # 剧情简介
    summary_tag = soup.select_one('span[property="v:summary"]') or soup.select_one('.all.hidden')
    if summary_tag:
        data['summary'] = summary_tag.get_text(strip=True)

    # 海报图片
    poster_tag = soup.select_one('#mainpic img')
    if poster_tag:
        data['poster_url'] = poster_tag.get('src', '')

    return data
