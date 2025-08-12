from flask import Flask
from flask_cors import CORS
from flask_session import Session
import os

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['JSON_AS_ASCII'] = False
    
    # 初始化扩展
    Session(app)
    CORS(app, supports_credentials=True)
    
    # 注册蓝图
    from app.routes import auth, api, admin, mp, static
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(mp.bp)
    app.register_blueprint(static.bp)
    
    return app 