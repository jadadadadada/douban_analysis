# 电影相关接口
from flask import Blueprint, request, jsonify
import db.dao as dao

movies_bp = Blueprint('movies', __name__)


def success_response(data, msg='success'):
    """成功响应"""
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=400):
    """错误响应"""
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


def normalize_page_params(page, size, max_size=100):
    """规范分页参数，避免负数页码和过大分页影响数据库"""
    page = max(page or 1, 1)
    size = max(size or 20, 1)
    size = min(size, max_size)
    return page, size


@movies_bp.route('/api/movies', methods=['GET'])
def get_movies():
    """获取电影列表（分页+筛选）"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        genre = request.args.get('genre')
        year = request.args.get('year', type=int)
        min_rating = request.args.get('min_rating', type=float)
        country = request.args.get('country')

        page, size = normalize_page_params(page, size)
        result = dao.get_movies(page, size, genre, year, min_rating, country)
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 500)


@movies_bp.route('/api/movies/search', methods=['GET'])
def search_movies():
    """关键词搜索电影"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword.strip():
            return error_response('搜索关键词不能为空')

        movies = dao.search_movies(keyword)
        return success_response(movies)
    except Exception as e:
        return error_response(str(e), 500)


@movies_bp.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie_detail(movie_id):
    """获取电影详情"""
    try:
        movie = dao.get_movie_by_id(movie_id)
        if not movie:
            return error_response('电影不存在', 404)
        return success_response(movie)
    except Exception as e:
        return error_response(str(e), 500)
