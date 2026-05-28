# 用户认证接口
from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import db.dao as dao

auth_bp = Blueprint('auth', __name__)


def success_response(data, msg='success'):
    return jsonify({'code': 200, 'data': data, 'msg': msg})


def error_response(msg, code=400):
    return jsonify({'code': code, 'data': None, 'msg': msg}), code


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return error_response('请求数据为空')

    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip() or None

    if not username or not password:
        return error_response('用户名和密码不能为空')
    if len(username) < 2 or len(username) > 50:
        return error_response('用户名长度需在 2-50 之间')
    if len(password) < 3:
        return error_response('密码长度不能少于 3 位')

    # 检查用户名是否已存在
    if dao.get_user_by_username(username):
        return error_response('用户名已存在')

    password_hash = generate_password_hash(password)
    user_id = dao.insert_user(username, password_hash, email)

    # 自动登录
    session['user_id'] = user_id
    session['username'] = username

    return success_response({'user_id': user_id, 'username': username}, '注册成功')


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return error_response('请求数据为空')

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response('用户名和密码不能为空')

    user = dao.get_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return error_response('用户名或密码错误')

    session['user_id'] = user['id']
    session['username'] = user['username']

    return success_response({'user_id': user['id'], 'username': user['username']}, '登录成功')


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return success_response(None, '已退出登录')


@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    """获取当前用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return success_response(None)

    user = dao.get_user_by_id(user_id)
    if not user:
        session.clear()
        return success_response(None)

    return success_response({
        'user_id': user['id'],
        'username': user['username'],
        'email': user.get('email')
    })
