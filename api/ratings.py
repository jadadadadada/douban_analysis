# 用户评分接口
from flask import Blueprint, request, session, jsonify
import db.dao as dao

ratings_bp = Blueprint('ratings', __name__)


def success_response(data, msg='success'):
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=400):
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


def get_current_user_id():
    return session.get('user_id')


def normalize_page_params(page, size, max_size=100):
    """规范分页参数"""
    page = max(page or 1, 1)
    size = min(max(size or 20, 1), max_size)
    return page, size


@ratings_bp.route('/api/ratings', methods=['POST'])
def rate_movie():
    """给电影评分"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    data = request.get_json()
    if not data:
        return error_response('请求数据为空')

    movie_id = data.get('movie_id')
    rating = data.get('rating')

    if not movie_id:
        return error_response('电影 ID 不能为空')
    if rating is None:
        return error_response('评分不能为空')

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return error_response('评分必须是数字')

    if rating < 1.0 or rating > 5.0:
        return error_response('评分范围为 1.0-5.0')

    dao.add_or_update_rating(user_id, movie_id, rating)
    return success_response({'rating': rating}, '评分成功')


@ratings_bp.route('/api/ratings/<int:movie_id>', methods=['DELETE'])
def remove_my_rating(movie_id):
    """取消当前用户对某部电影的评分"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    dao.remove_rating(user_id, movie_id)
    return success_response({'rating': None}, '已取消评分')


@ratings_bp.route('/api/ratings/<int:movie_id>', methods=['GET'])
def get_movie_ratings(movie_id):
    """获取电影的用户评分列表"""
    ratings = dao.get_movie_user_ratings(movie_id)

    # 计算平均用户评分
    if ratings:
        avg = sum(float(r['rating']) for r in ratings) / len(ratings)
    else:
        avg = None

    return success_response({
        'ratings': ratings,
        'avg_rating': round(avg, 1) if avg else None,
        'count': len(ratings)
    })


@ratings_bp.route('/api/ratings/my', methods=['GET'])
def get_my_ratings():
    """获取我的评分列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    page, size = normalize_page_params(page, size)
    data = dao.get_user_ratings_list(user_id, page, size)
    return success_response(data)


@ratings_bp.route('/api/ratings/<int:movie_id>/my', methods=['GET'])
def get_my_rating(movie_id):
    """获取我对某部电影的评分"""
    user_id = get_current_user_id()
    if not user_id:
        return success_response({'rating': None})

    rating = dao.get_user_rating(user_id, movie_id)
    return success_response({'rating': rating})
