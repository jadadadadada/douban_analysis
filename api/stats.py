# 统计分析接口
from flask import Blueprint, request, jsonify
import db.dao as dao
from analysis.analyzer import MovieAnalyzer

stats_bp = Blueprint('stats', __name__)

# 全局分析器实例
_analyzer = None


def get_analyzer():
    """获取分析器实例（延迟初始化）"""
    global _analyzer
    if _analyzer is None:
        _analyzer = MovieAnalyzer()
        _analyzer.load_data()
    return _analyzer


def success_response(data, msg='success'):
    """成功响应"""
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=500):
    """错误响应"""
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


def normalize_limit(value, default=20, max_limit=100):
    """规范排行榜数量，避免单次请求过大"""
    value = value or default
    return min(max(value, 1), max_limit)


def get_filter_params():
    """从请求中提取筛选参数"""
    return {
        'genre': request.args.get('genre', None),
        'year': request.args.get('year', None, type=int),
        'country': request.args.get('country', None),
        'min_rating': request.args.get('min_rating', None, type=float)
    }


@stats_bp.route('/api/stats/genre-distribution', methods=['GET'])
def genre_distribution():
    """各类型电影数量（饼图）"""
    try:
        filters = get_filter_params()
        data = dao.get_genre_distribution(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/rating-distribution', methods=['GET'])
def rating_distribution():
    """评分区间分布（柱状图）"""
    try:
        filters = get_filter_params()
        data = dao.get_rating_distribution(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/year-trend', methods=['GET'])
def year_trend():
    """年代电影数量与均分趋势（折线图）"""
    try:
        filters = get_filter_params()
        data = dao.get_year_trend(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/country-distribution', methods=['GET'])
def country_distribution():
    """各国/地区电影数量（地图）"""
    try:
        filters = get_filter_params()
        data = dao.get_country_distribution(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/top-rated', methods=['GET'])
def top_rated():
    """评分最高电影（排行榜）"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = normalize_limit(limit)
        filters = get_filter_params()
        data = dao.get_top_rated(limit, **filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/genre-year-heatmap', methods=['GET'])
def genre_year_heatmap():
    """年份×类型矩阵（热力图）"""
    try:
        filters = get_filter_params()
        data = dao.get_genre_year_heatmap(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/director-network', methods=['GET'])
def director_network():
    """导演-演员协作关系（关系图）"""
    try:
        filters = get_filter_params()
        data = dao.get_director_network(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/summary-wordcloud', methods=['GET'])
def summary_wordcloud():
    """简介关键词词频（词云）"""
    try:
        filters = get_filter_params()
        analyzer = get_analyzer()
        data = analyzer.generate_wordcloud_data(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/duration-rating', methods=['GET'])
def duration_rating():
    """时长 vs 评分相关性（散点图）"""
    try:
        filters = get_filter_params()
        data = dao.get_duration_rating_data(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@stats_bp.route('/api/stats/summary-stats', methods=['GET'])
def summary_stats():
    """核心指标统计"""
    try:
        filters = get_filter_params()
        data = dao.get_summary_stats(**filters)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))
