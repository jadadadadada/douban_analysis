# 数据分析模块 - 基于 pandas 的多维分析
import pandas as pd
import jieba
import re
from collections import Counter
import db.dao as dao
from db.connection import get_connection, close_connection


# 停用词列表
STOP_WORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '他', '她', '它', '们', '那', '被', '从', '对', '但', '以', '为',
    '与', '把', '让', '用', '之', '而', '等', '或', '中', '个', '大', '小', '多',
    '少', '来', '这个', '那个', '什么', '怎么', '如何', '为什么', '因为', '所以',
    '如果', '虽然', '但是', '可以', '已经', '还是', '不是', '没有', '开始', '最后',
    '一个', '两个', '世界', '生活', '故事', '影片', '电影', '导演', '演员', '拍摄'
])


class MovieAnalyzer:
    """电影数据分析器"""

    def __init__(self):
        self.movies_df = None

    def load_data(self):
        """从数据库加载数据为 DataFrame"""
        conn = get_connection()
        try:
            sql = """
                SELECT m.id, m.douban_id, m.title, m.year, m.rating,
                       m.rating_count, m.duration_minutes, m.summary
                FROM movies m
                WHERE m.rating IS NOT NULL
            """
            self.movies_df = pd.read_sql(sql, conn)

            # 加载关联数据
            genres_sql = """
                SELECT mg.movie_id, g.name as genre
                FROM movie_genres mg
                JOIN genres g ON mg.genre_id = g.id
            """
            genres_df = pd.read_sql(genres_sql, conn)
            self.genres_df = genres_df

            countries_sql = """
                SELECT mc.movie_id, c.name as country
                FROM movie_countries mc
                JOIN countries c ON mc.country_id = c.id
            """
            self.countries_df = pd.read_sql(countries_sql, conn)

        finally:
            close_connection(conn)

    def get_genre_stats(self):
        """类型统计"""
        if self.genres_df is None:
            self.load_data()
        genre_counts = self.genres_df['genre'].value_counts().reset_index()
        genre_counts.columns = ['name', 'count']
        return genre_counts.to_dict('records')

    def get_rating_stats(self):
        """评分分析"""
        if self.movies_df is None:
            self.load_data()
        bins = [0, 5, 6, 7, 8, 9, 10]
        labels = ['0-5分', '5-6分', '6-7分', '7-8分', '8-9分', '9-10分']
        self.movies_df['rating_range'] = pd.cut(
            self.movies_df['rating'], bins=bins, labels=labels, right=True
        )
        rating_counts = self.movies_df['rating_range'].value_counts().reindex(labels, fill_value=0)
        return [{'name': label, 'count': int(count)} for label, count in rating_counts.items()]

    def get_year_trend_stats(self):
        """年代趋势"""
        if self.movies_df is None:
            self.load_data()
        df = self.movies_df[self.movies_df['year'] >= 1970].copy()
        year_stats = df.groupby('year').agg(
            count=('id', 'count'),
            avg_rating=('rating', 'mean')
        ).reset_index()
        year_stats['avg_rating'] = year_stats['avg_rating'].round(1)
        return year_stats.to_dict('records')

    def get_country_stats(self):
        """国家分布"""
        if self.countries_df is None:
            self.load_data()
        country_counts = self.countries_df['country'].value_counts().head(30).reset_index()
        country_counts.columns = ['name', 'count']
        return country_counts.to_dict('records')

    def get_duration_rating_correlation(self):
        """时长与评分相关性"""
        if self.movies_df is None:
            self.load_data()
        df = self.movies_df[
            (self.movies_df['duration_minutes'].notna()) &
            (self.movies_df['rating'].notna()) &
            (self.movies_df['duration_minutes'] > 0) &
            (self.movies_df['duration_minutes'] < 300)
        ].copy()
        return df[['duration_minutes', 'rating']].to_dict('records')

    def generate_wordcloud_data(self, top_n=100, genre=None, year=None, country=None, min_rating=None):
        """jieba 分词 + 词频统计"""
        # 通过 DAO 获取筛选后的简介
        rows = dao.get_all_summaries(genre, year, country, min_rating)
        summaries = [row['summary'] for row in rows if row['summary']]
        all_text = ''.join(summaries)

        # 清理文本
        all_text = re.sub(r'[^一-龥a-zA-Z0-9]', ' ', all_text)

        # jieba 分词
        words = jieba.cut(all_text)

        # 过滤停用词和短词
        filtered_words = [
            w for w in words
            if len(w) >= 2 and w not in STOP_WORDS
        ]

        # 统计词频
        word_counts = Counter(filtered_words)
        top_words = word_counts.most_common(top_n)

        return [{'name': word, 'value': count} for word, count in top_words]
