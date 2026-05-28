# 筛选选项接口
from flask import Blueprint, jsonify
import db.dao as dao

filters_bp = Blueprint('filters', __name__)


def success_response(data, msg='success'):
    """成功响应"""
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=500):
    """错误响应"""
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


@filters_bp.route('/api/filters/genres', methods=['GET'])
def get_genres():
    """返回所有类型"""
    try:
        data = dao.get_all_genres()
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@filters_bp.route('/api/filters/years', methods=['GET'])
def get_years():
    """返回所有年份"""
    try:
        data = dao.get_all_years()
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@filters_bp.route('/api/filters/countries', methods=['GET'])
def get_countries():
    """返回所有国家"""
    try:
        data = dao.get_all_countries()
        return success_response(data)
    except Exception as e:
        return error_response(str(e))
