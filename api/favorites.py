# 用户收藏接口
from flask import Blueprint, request, session, jsonify
import db.dao as dao

favorites_bp = Blueprint('favorites', __name__)


def success_response(data, msg='success'):
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=400):
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


def get_current_user_id():
    """获取当前登录用户 ID"""
    return session.get('user_id')


def normalize_page_params(page, size, max_size=100):
    """规范分页参数"""
    page = max(page or 1, 1)
    size = min(max(size or 20, 1), max_size)
    return page, size


@favorites_bp.route('/api/favorites', methods=['POST'])
def add_favorite():
    """收藏电影"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    data = request.get_json()
    movie_id = data.get('movie_id') if data else None
    if not movie_id:
        return error_response('电影 ID 不能为空')

    result = dao.add_favorite(user_id, movie_id)
    return success_response({'favorited': True}, '收藏成功')


@favorites_bp.route('/api/favorites/<int:movie_id>', methods=['DELETE'])
def remove_favorite(movie_id):
    """取消收藏"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    result = dao.remove_favorite(user_id, movie_id)
    return success_response({'favorited': False}, '已取消收藏')


@favorites_bp.route('/api/favorites', methods=['GET'])
def get_favorites():
    """获取我的收藏列表"""
    user_id = get_current_user_id()
    if not user_id:
        return error_response('请先登录', 401)

    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    page, size = normalize_page_params(page, size)
    data = dao.get_user_favorites(user_id, page, size)
    return success_response(data)


@favorites_bp.route('/api/favorites/<int:movie_id>/status', methods=['GET'])
def check_favorite(movie_id):
    """检查是否已收藏"""
    user_id = get_current_user_id()
    if not user_id:
        return success_response({'favorited': False})

    favorited = dao.is_favorited(user_id, movie_id)
    return success_response({'favorited': favorited})
