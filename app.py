# Flask 应用入口
from flask import Flask, render_template, jsonify, session, Response, request
from api.movies import movies_bp
from api.stats import stats_bp
from api.filters import filters_bp
from api.auth import auth_bp
from api.favorites import favorites_bp
from api.ratings import ratings_bp
import config
import requests as http_requests


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)

    # Session 配置
    app.secret_key = config.SECRET_KEY

    # 注册 Blueprint
    app.register_blueprint(movies_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(ratings_bp)

    # 主页面路由
    @app.route('/')
    def index():
        return render_template('index.html')

    # 海报图片代理（绕过豆瓣防盗链）
    @app.route('/api/proxy/poster')
    def proxy_poster():
        url = request.args.get('url', '')
        if not url or not url.startswith('https://img'):
            return '', 400
        try:
            headers = {
                'Referer': 'https://movie.douban.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = http_requests.get(url, headers=headers, timeout=5, verify=False)
            if resp.status_code == 200:
                return Response(resp.content, content_type=resp.headers.get('Content-Type', 'image/jpeg'))
        except Exception:
            pass
        return '', 404

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'code': 400, 'data': None, 'msg': '请求参数错误'}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'code': 401, 'data': None, 'msg': '请先登录'}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'data': None, 'msg': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'code': 500, 'data': None, 'msg': '服务器内部错误'}), 500

    return app


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
