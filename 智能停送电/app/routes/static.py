from flask import Blueprint, jsonify, send_from_directory
import logging
import os

bp = Blueprint("static", __name__)
logger = logging.getLogger(__name__)


def send_html_no_cache(directory, filename):
    response = send_from_directory(directory, filename)
    if filename.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@bp.route("/")
def index():
    """返回登录页。"""
    try:
        current_dir = os.getcwd()
        web_pages_dir = os.path.join(current_dir, "web_pages")
        return send_html_no_cache(web_pages_dir, "login.html")
    except Exception:
        logger.exception("首页加载失败")
        return jsonify({"msg": "首页加载失败"}), 500


@bp.route("/<path:filename>")
def serve_html(filename):
    """提供静态页面文件。"""
    if filename.startswith("api/"):
        return jsonify({"msg": "API 路径"}), 404

    current_dir = os.getcwd()
    web_pages_dir = os.path.join(current_dir, "web_pages")
    file_path = os.path.join(web_pages_dir, filename)

    if os.path.exists(file_path):
        return send_html_no_cache(web_pages_dir, filename)

    html_file = filename + ".html"
    html_path = os.path.join(web_pages_dir, html_file)
    if os.path.exists(html_path):
        return send_html_no_cache(web_pages_dir, html_file)

    return jsonify({"msg": "页面不存在"}), 404
