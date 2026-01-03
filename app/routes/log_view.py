from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from app.config import Config
import os
import re
from flask_login import login_required, current_user

log_view = Blueprint('log_view', __name__, url_prefix='/logs')

@log_view.route('/')
@login_required
def index():
    """日志查看主页"""
    # 检查是否为管理员
    if not current_user.is_admin():
        flash('无权限访问该页面', 'danger')
        return redirect(url_for('auth.login'))
        
    # 获取日志文件路径
    log_file = Config.LOG_FILE
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        return render_template('logs.html', logs=[], error="日志文件不存在")
    
    # 获取请求参数
    lines = request.args.get('lines', 100, type=int)
    search = request.args.get('search', '')
    
    try:
        # 读取日志文件的最后N行，使用GBK编码处理中文日志
        with open(log_file, 'r', encoding='gbk') as f:
            all_logs = f.readlines()
        
        # 如果有搜索关键词，过滤日志
        if search:
            search_regex = re.compile(search, re.IGNORECASE)
            filtered_logs = [log for log in all_logs if search_regex.search(log)]
        else:
            filtered_logs = all_logs
        
        # 只显示最后N行
        recent_logs = filtered_logs[-lines:]
        
        return render_template('logs.html', logs=recent_logs, lines=lines, search=search)
    except Exception as e:
        current_app.logger.error(f"读取日志文件时出错: {e}")
        return render_template('logs.html', logs=[], error=f"读取日志文件时出错: {e}")

@log_view.route('/clear')
def clear_logs():
    """清空日志文件"""
    try:
        # 清空日志文件，使用GBK编码
        with open(Config.LOG_FILE, 'w', encoding='gbk') as f:
            f.write('')
        return render_template('logs.html', logs=[], message="日志已清空")
    except Exception as e:
        current_app.logger.error(f"清空日志文件时出错: {e}")
        return render_template('logs.html', logs=[], error=f"清空日志文件时出错: {e}")
