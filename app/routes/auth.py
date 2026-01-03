from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from app.models import User, Admin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# 创建蓝图
bp = Blueprint('auth', __name__)

# 登录管理器配置
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """根据用户ID加载用户或管理员
    ID格式：user_1 或 admin_1
    """
    try:
        if user_id.startswith('admin_'):
            # 加载管理员
            admin_id = int(user_id.split('_')[1])
            return Admin.query.get(admin_id)
        elif user_id.startswith('user_'):
            # 加载普通用户
            user_id_num = int(user_id.split('_')[1])
            return User.query.get(user_id_num)
        # 处理旧格式ID（兼容原有数据）
        return User.query.get(int(user_id))
    except (ValueError, IndexError):
        return None

@bp.record_once
def on_load(state):
    login_manager.init_app(state.app)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 表单验证
        if not username or not email or not password or not confirm_password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('两次密码不一致', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('auth.register'))
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 获取登录信息
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # 表单验证
        if not email or not password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.login'))
        
        # 先检查是否为管理员登录
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            # 管理员登录成功
            login_user(admin)
            flash('管理员登录成功！', 'success')
            # 记录管理员登录日志
            current_app.logger.info(f"管理员登录成功: {email} from {ip_address}")
            return redirect(url_for('visualizations.system_menu'))
        
        # 检查是否为普通用户登录
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # 用户登录成功
            login_user(user)
            flash('用户登录成功！', 'success')
            
            # 记录用户登录历史
            from app.models import LoginHistory
            login_history = LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                login_result=True
            )
            db.session.add(login_history)
            db.session.commit()
            
            # 记录用户登录日志
            current_app.logger.info(f"用户登录成功: {email} from {ip_address}")
            return redirect(url_for('visualizations.system_menu'))
        
        # 分析登录失败原因
        login_fail_reason = ""
        
        # 检查是否为管理员
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            if not admin.check_password(password):
                login_fail_reason = "管理员密码错误"
            elif not admin.is_active:
                login_fail_reason = "管理员账号已禁用"
            else:
                login_fail_reason = "管理员登录未知错误"
        else:
            # 检查是否为普通用户
            user = User.query.filter_by(email=email).first()
            if user:
                if not user.check_password(password):
                    login_fail_reason = "用户密码错误"
                elif not user.is_active:
                    login_fail_reason = "用户账号已禁用"
                else:
                    login_fail_reason = "用户登录未知错误"
            else:
                login_fail_reason = "邮箱不存在"
        
        # 显示登录失败信息
        flash('登录失败: ' + login_fail_reason, 'danger')
        
        # 记录登录失败日志
        current_app.logger.warning(f"登录失败: {email} from {ip_address} - 原因: {login_fail_reason}")
        
        # 记录登录失败历史（如果用户存在）
        user = User.query.filter_by(email=email).first()
        if user:
            from app.models import LoginHistory
            login_history = LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                login_result=False,
                fail_reason=login_fail_reason
            )
            db.session.add(login_history)
            db.session.commit()
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 获取用户信息用于日志记录
    user_info = f"{current_user.username} ({current_user.email})"
    user_type = "管理员" if current_user.is_admin() else "用户"
    
    # 记录登出日志
    current_app.logger.info(f"{user_type}登出成功: {user_info} from {request.remote_addr}")
    
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('visualizations.index'))
