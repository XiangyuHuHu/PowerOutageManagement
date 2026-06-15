import os
import logging
import time
from pathlib import Path


def _load_dotenv_from_file():
    """在建立数据库连接之前，把项目根目录 .env 写入 os.environ。"""
    root = Path(__file__).resolve().parent.parent
    for env_path in (root / ".env", Path.cwd() / ".env"):
        if env_path.is_file():
            break
    else:
        return
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            os.environ[key] = value


_load_dotenv_from_file()

from flask import Flask
from flask_cors import CORS
from flask_session import Session


def setup_logging():
    """配置应用日志（避免重复添加handler）"""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )


def apply_session_config(app):
    """会话配置：默认filesystem，可通过环境变量切换。"""
    session_type = os.environ.get('SESSION_TYPE', 'filesystem').lower()
    app.config['SESSION_TYPE'] = session_type
    app.config['SESSION_PERMANENT'] = False

    if session_type == 'filesystem':
        session_file_dir = os.environ.get('SESSION_FILE_DIR')
        if session_file_dir:
            app.config['SESSION_FILE_DIR'] = session_file_dir
        return

    if session_type == 'redis':
        session_redis_url = os.environ.get('SESSION_REDIS_URL')
        if not session_redis_url:
            logging.getLogger(__name__).warning(
                "SESSION_TYPE=redis 但未配置 SESSION_REDIS_URL，已回退到 filesystem"
            )
            app.config['SESSION_TYPE'] = 'filesystem'
            return
        try:
            import redis
            app.config['SESSION_REDIS'] = redis.from_url(session_redis_url)
        except Exception:
            logging.getLogger(__name__).exception(
                "Redis Session 初始化失败，已回退到 filesystem"
            )
            app.config['SESSION_TYPE'] = 'filesystem'
        return

    logging.getLogger(__name__).warning(
        "不支持的 SESSION_TYPE=%s，已回退到 filesystem", session_type
    )
    app.config['SESSION_TYPE'] = 'filesystem'

def create_app():
    """创建Flask应用"""
    setup_logging()
    app = Flask(__name__)
    
    # 基础配置
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    apply_session_config(app)
    app.config['JSON_AS_ASCII'] = False
    
    # 初始化扩展
    Session(app)
    CORS(app, supports_credentials=True)

    @app.before_request
    def log_request_start():
        from flask import g
        g._request_start_time = time.time()

    @app.after_request
    def log_request_result(response):
        from flask import request, g
        elapsed_ms = int((time.time() - getattr(g, '_request_start_time', time.time())) * 1000)
        logging.getLogger("request").info(
            "%s %s -> %s (%dms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms
        )
        return response
    
    # 注册蓝图
    from app.routes import auth, operations, approvals, admin, static
    app.register_blueprint(auth.bp)
    app.register_blueprint(operations.bp)
    app.register_blueprint(approvals.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(static.bp)
    
    return app 