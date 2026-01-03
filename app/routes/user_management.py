from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import User, Admin
from app import db
from flask_login import login_required, current_user

user_management = Blueprint('user_management', __name__, url_prefix='/admin')


@user_management.route('/users')
@login_required
def index():
    """用户管理主页"""
    # 检查是否为管理员
    if not current_user.is_admin():
        flash('无权限访问该页面', 'danger')
        return redirect(url_for('visualizations.index'))
    
    # 获取所有普通用户，按照ID升序排序
    users = User.query.order_by(User.id.asc()).all()
    
    return render_template('admin/users.html', users=users)


@user_management.route('/users/activate/<int:user_id>')
@login_required
def activate_user(user_id):
    """激活用户"""
    if not current_user.is_admin():
        flash('无权限执行该操作', 'danger')
        return redirect(url_for('visualizations.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    flash(f'用户 {user.username} 已激活', 'success')
    return redirect(url_for('user_management.index'))


@user_management.route('/users/deactivate/<int:user_id>')
@login_required
def deactivate_user(user_id):
    """停用用户"""
    if not current_user.is_admin():
        flash('无权限执行该操作', 'danger')
        return redirect(url_for('visualizations.index'))
    
    # 只有当当前登录的是普通用户时，才需要检查是否是自己的账号
    # 管理员可以停用任何普通用户，包括ID相同的用户
    from app.models import User
    if isinstance(current_user, User) and user_id == current_user.id:
        flash('不能停用自己的账号', 'danger')
        return redirect(url_for('user_management.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    flash(f'用户 {user.username} 已停用', 'success')
    return redirect(url_for('user_management.index'))


@user_management.route('/users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    """删除用户"""
    if not current_user.is_admin():
        flash('无权限执行该操作', 'danger')
        return redirect(url_for('visualizations.index'))
    
    # 只有当当前登录的是普通用户时，才需要检查是否是自己的账号
    # 管理员可以删除任何普通用户，包括ID相同的用户
    from app.models import User
    if isinstance(current_user, User) and user_id == current_user.id:
        flash('不能删除自己的账号', 'danger')
        return redirect(url_for('user_management.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'用户 {user.username} 已删除', 'success')
    return redirect(url_for('user_management.index'))


# 注意：由于管理员和普通用户现已分离为不同表，提升/降级功能已不再适用
# 管理员账号管理可通过数据库直接操作或后续扩展
# 以下函数已注释，不再使用

# @user_management.route('/users/promote/<int:user_id>')
# @login_required
# def promote_user(user_id):
#     """提升为管理员"""
#     if not current_user.is_admin():
#         flash('无权限执行该操作', 'danger')
#         return redirect(url_for('visualizations.index'))
#     
#     # 提升用户为管理员需要在admin表中创建新记录
#     # 这里简化处理，实际实现需要更复杂的逻辑
#     flash('提升功能暂未实现', 'info')
#     return redirect(url_for('user_management.index'))

# @user_management.route('/users/demote/<int:user_id>')
# @login_required
# def demote_user(user_id):
#     """降级为普通用户"""
#     if not current_user.is_admin():
#         flash('无权限执行该操作', 'danger')
#         return redirect(url_for('visualizations.index'))
#     
#     # 降级管理员为普通用户需要从admin表中删除记录
#     # 这里简化处理，实际实现需要更复杂的逻辑
#     flash('降级功能暂未实现', 'info')
#     return redirect(url_for('user_management.index'))
