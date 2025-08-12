from flask import Blueprint, send_from_directory, request, jsonify
import os

bp = Blueprint('static', __name__)

@bp.route('/')
def index():
    """首页重定向"""
    try:
        import os
        current_dir = os.getcwd()
        web_pages_dir = os.path.join(current_dir, 'web_pages')
        return send_from_directory(web_pages_dir, 'login.html')
    except Exception as e:
        print(f"首页加载失败: {e}")
        return jsonify({"msg": "首页加载失败"}), 500

@bp.route('/<path:filename>')
def serve_html(filename):
    """提供HTML文件服务"""
    # API路径不处理，让其他路由处理
    if filename.startswith('api/'):
        return jsonify({"msg": "API路径"}), 404
    
    # 检查文件是否存在
    current_dir = os.getcwd()
    web_pages_dir = os.path.join(current_dir, 'web_pages')
    file_path = os.path.join(web_pages_dir, filename)
    
    if os.path.exists(file_path):
        return send_from_directory(web_pages_dir, filename)
    else:
        # 如果文件不存在，尝试添加.html后缀
        html_file = filename + '.html'
        html_path = os.path.join(web_pages_dir, html_file)
        
        if os.path.exists(html_path):
            return send_from_directory(web_pages_dir, html_file)
        else:
            return jsonify({"msg": "页面不存在"}), 404 