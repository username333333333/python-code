from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from app.models import User, LoginHistory, Favorite
from app import db
from flask_login import login_required, current_user
import json

user_profile = Blueprint('user_profile', __name__, url_prefix='/user')


@user_profile.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('user/profile.html')


@user_profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑用户个人资料"""
    if request.method == 'POST':
        # 获取表单数据
        nickname = request.form.get('nickname')
        email = request.form.get('email')
        avatar = request.form.get('avatar', '')
        
        # 表单验证
        if not nickname or not email:
            flash('昵称和邮箱不能为空', 'danger')
            return redirect(url_for('user_profile.edit_profile'))
        
        # 检查邮箱是否已被使用
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('该邮箱已被注册', 'danger')
                return redirect(url_for('user_profile.edit_profile'))
        
        # 更新用户资料
        current_user.nickname = nickname
        current_user.email = email
        if avatar:  # 只在提供了新头像时更新
            current_user.avatar = avatar
        
        db.session.commit()
        flash('个人资料更新成功', 'success')
        return redirect(url_for('user_profile.profile'))
    
    return render_template('user/edit_profile.html')


@user_profile.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        # 获取表单数据
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 表单验证
        if not old_password or not new_password or not confirm_password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('user_profile.change_password'))
        
        # 检查旧密码是否正确
        if not current_user.check_password(old_password):
            flash('原密码错误', 'danger')
            return redirect(url_for('user_profile.change_password'))
        
        # 检查新密码和确认密码是否一致
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('user_profile.change_password'))
        
        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('user_profile.profile'))
    
    return render_template('user/change_password.html')


@user_profile.route('/login_history')
@login_required
def login_history():
    """登录历史记录"""
    # 分页显示登录历史
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取当前用户的登录历史
    history = LoginHistory.query.filter_by(user_id=current_user.id)
    history = history.order_by(LoginHistory.login_time.desc())
    pagination = history.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('user/login_history.html', pagination=pagination)


@user_profile.route('/favorites')
@login_required
def favorites():
    """用户收藏夹"""
    # 分页显示收藏夹
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取筛选条件
    favorite_type = request.args.get('favorite_type')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 获取当前用户的收藏，根据用户类型过滤
    if current_user.is_admin():
        # 管理员收藏
        admin_id = int(current_user.get_id().split('_')[1])
        favorites = Favorite.query.filter_by(admin_id=admin_id)
    else:
        # 普通用户收藏
        user_id = int(current_user.get_id().split('_')[1])
        favorites = Favorite.query.filter_by(user_id=user_id)
    
    # 应用筛选条件
    # 收藏类型筛选
    if favorite_type:
        favorites = favorites.filter_by(favorite_type=favorite_type)
    
    # 搜索框筛选
    if search:
        favorites = favorites.filter(Favorite.name.like(f'%{search}%'))
    
    # 开始日期筛选
    if start_date:
        favorites = favorites.filter(Favorite.created_at >= start_date)
    
    # 结束日期筛选
    if end_date:
        favorites = favorites.filter(Favorite.created_at <= end_date)
    
    favorites = favorites.order_by(Favorite.created_at.desc())
    pagination = favorites.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('user/favorites.html', pagination=pagination)


@user_profile.route('/favorites/add', methods=['POST'])
@login_required
def add_favorite():
    """添加收藏"""
    try:
        # 获取收藏数据
        data = request.get_json()
        favorite_type = data.get('type')
        name = data.get('name')
        content = data.get('content')
        
        # 验证数据
        if not favorite_type or not name or not content:
            return json.dumps({'success': False, 'message': '收藏数据不完整'}), 400
        
        # 创建收藏记录，根据用户类型设置不同的ID字段
        if current_user.is_admin():
            # 管理员收藏
            favorite = Favorite(
                admin_id=int(current_user.get_id().split('_')[1]),
                favorite_type=favorite_type,
                name=name,
                content=content
            )
        else:
            # 普通用户收藏
            favorite = Favorite(
                user_id=int(current_user.get_id().split('_')[1]),
                favorite_type=favorite_type,
                name=name,
                content=content
            )
        
        db.session.add(favorite)
        db.session.commit()
        
        return json.dumps({'success': True, 'message': '收藏成功'})
    except Exception as e:
        current_app.logger.error(f"添加收藏失败: {e}")
        return json.dumps({'success': False, 'message': '添加收藏失败'}), 500


@user_profile.route('/favorites/delete/<int:favorite_id>')
@login_required
def delete_favorite(favorite_id):
    """删除收藏"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    # 检查是否是当前用户的收藏，根据用户类型验证
    if current_user.is_admin():
        # 管理员只能删除自己的收藏
        admin_id = int(current_user.get_id().split('_')[1])
        if favorite.admin_id != admin_id:
            flash('无权限删除该收藏', 'danger')
            return redirect(url_for('user_profile.favorites'))
    else:
        # 普通用户只能删除自己的收藏
        user_id = int(current_user.get_id().split('_')[1])
        if favorite.user_id != user_id:
            flash('无权限删除该收藏', 'danger')
            return redirect(url_for('user_profile.favorites'))
    
    db.session.delete(favorite)
    db.session.commit()
    flash('收藏已删除', 'success')
    return redirect(url_for('user_profile.favorites'))


@user_profile.route('/favorites/detail/<int:favorite_id>')
@login_required
def favorite_detail(favorite_id):
    """查看收藏详情"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    # 检查是否是当前用户的收藏，根据用户类型验证
    if current_user.is_admin():
        # 管理员只能查看自己的收藏
        admin_id = int(current_user.get_id().split('_')[1])
        if favorite.admin_id != admin_id:
            flash('无权限查看该收藏', 'danger')
            return redirect(url_for('user_profile.favorites'))
    else:
        # 普通用户只能查看自己的收藏
        user_id = int(current_user.get_id().split('_')[1])
        if favorite.user_id != user_id:
            flash('无权限查看该收藏', 'danger')
            return redirect(url_for('user_profile.favorites'))
    
    # 直接使用收藏内容对象，不需要转换为JSON字符串
    content = favorite.content
    
    # 如果是数据查询类型的收藏，根据查询条件重新执行查询
    if favorite.favorite_type == 'query':
        try:
            import pandas as pd
            from app.utils.data_loader import load_all_city_data
            
            # 加载所有城市数据
            df = load_all_city_data()
            
            # 构建查询条件
            filters = {
                'city': content.get('city', ''),
                'start_date': content.get('start_date', ''),
                'end_date': content.get('end_date', ''),
                'weather': content.get('weather', ''),
                'wind_dir': content.get('wind_dir', ''),
                'wind_lvl': content.get('wind_lvl', ''),
                'time_period': content.get('time_period', ''),
                'temp_min': content.get('temp_min', ''),
                'temp_max': content.get('temp_max', ''),
            }
            
            # ✅ 筛选逻辑（使用布尔掩码）
            mask = pd.Series(True, index=df.index)
            
            # 城市筛选
            if filters["city"] and '城市' in df.columns:
                mask &= df["城市"] == filters["city"]
            
            # 日期筛选
            if '日期' in df.columns:
                if filters["start_date"]:
                    try:
                        start_date = pd.to_datetime(filters["start_date"])
                        mask &= df["日期"] >= start_date
                    except ValueError:
                        pass
                
                if filters["end_date"]:
                    try:
                        end_date = pd.to_datetime(filters["end_date"])
                        mask &= df["日期"] <= end_date
                    except ValueError:
                        pass
            
            # 天气状况、风向、风力筛选（根据时间段统一处理）
            if filters["weather"] or filters["wind_dir"] or filters["wind_lvl"]:
                # 初始化条件掩码
                combined_mask = pd.Series(False, index=df.index)
                
                # 根据时间段选择需要检查的时间段
                time_periods = []
                if filters["time_period"] == "day":
                    time_periods = ["白天"]
                elif filters["time_period"] == "night":
                    time_periods = ["夜间"]
                else:
                    time_periods = ["白天", "夜间"]
                
                # 对每个时间段检查所有筛选条件
                for period in time_periods:
                    # 初始化该时间段的条件掩码
                    period_mask = pd.Series(True, index=df.index)
                    
                    # 天气状况筛选
                    if filters["weather"]:
                        weather_col = f"天气状况({period})"
                        if weather_col in df.columns:
                            period_mask &= df[weather_col] == filters["weather"]
                        else:
                            period_mask = pd.Series(False, index=df.index)
                    
                    # 风向筛选
                    if filters["wind_dir"]:
                        wind_dir_col = f"风向({period})"
                        if wind_dir_col in df.columns:
                            period_mask &= df[wind_dir_col] == filters["wind_dir"]
                        else:
                            period_mask = pd.Series(False, index=df.index)
                    
                    # 风力筛选
                    if filters["wind_lvl"]:
                        wind_lvl_col = f"风力({period})"
                        if wind_lvl_col in df.columns:
                            period_mask &= df[wind_lvl_col] == filters["wind_lvl"]
                        else:
                            period_mask = pd.Series(False, index=df.index)
                    
                    # 将该时间段的条件掩码合并到总掩码中
                    combined_mask |= period_mask
                
                # 将合并后的条件掩码应用到主掩码中
                mask &= combined_mask
            
            # 温度筛选
            if filters["temp_min"] and '最低气温' in df.columns:
                try:
                    mask &= df["最低气温"] >= int(filters["temp_min"])
                except ValueError:
                    pass
            
            if filters["temp_max"] and '最高气温' in df.columns:
                try:
                    mask &= df["最高气温"] <= int(filters["temp_max"])
                except ValueError:
                    pass
            
            # 应用筛选
            filtered = df[mask]
            
            # 排序
            if '日期' in filtered.columns:
                filtered = filtered.sort_values("日期", ascending=False)
            
            # 取前20条数据
            page_data = filtered.iloc[:20].copy()
            
            # 清理字段名，去除空格
            page_data.columns = page_data.columns.str.strip()
            
            if '日期' in page_data.columns:
                # 确保日期列是datetime类型
                if not pd.api.types.is_datetime64_any_dtype(page_data['日期']):
                    page_data['日期'] = pd.to_datetime(page_data['日期'], errors='coerce')
                # 将日期转换为字符串格式
                page_data['日期'] = page_data['日期'].dt.strftime('%Y-%m-%d')
            
            # 将查询结果添加到收藏内容中
            content['results'] = page_data.to_dict(orient="records")
        except Exception as e:
            # 如果查询失败，添加错误信息
            content['error'] = f'查询执行失败: {str(e)}'
    # 如果是天气预测类型的收藏，根据预测条件重新生成预测结果
    elif favorite.favorite_type == 'prediction':
        try:
            from app.services.prediction_service import WeatherPredictionServiceFactory
            from app.utils.data_loader import load_attractions_data, load_all_city_data
            import pandas as pd
            import datetime
            from flask import current_app
            
            # 构建预测条件
            filters = {}
            if content.get('filters'):
                # 新版收藏格式，content包含filters字段
                filters['city'] = content['filters'].get('city', '')
                filters['days'] = content['filters'].get('days', '7')
            else:
                # 旧版收藏格式，content直接包含预测条件
                filters['city'] = content.get('city', '')
                filters['days'] = content.get('days', '7')
            
            # 确保city和days有值
            city = filters['city'] or '全部城市'
            days = int(filters['days']) if filters['days'] else 7
            
            # 加载所有城市的历史天气数据
            weather_df = load_all_city_data()
            
            # 创建预测服务实例
            prediction_service_factory = WeatherPredictionServiceFactory()
            prediction_service = prediction_service_factory.create_service(data_dir=current_app.config['DATA_DIR'])
            
            # 调用预测服务进行预测
            try:
                # 尝试直接预测
                predictions_df = prediction_service.predict_future(weather_df, city, days)
            except Exception as e:
                # 如果预测失败（可能是模型不存在），训练模型后重新预测
                current_app.logger.error(f"预测失败，尝试训练模型: {e}")
                prediction_service.train_all_models(weather_df)
                predictions_df = prediction_service.predict_future(weather_df, city, days)
            
            # 将预测结果转换为字典列表
            predictions = []
            if not predictions_df.empty:
                # 确保日期列是datetime类型
                if not pd.api.types.is_datetime64_any_dtype(predictions_df['日期']):
                    predictions_df['日期'] = pd.to_datetime(predictions_df['日期'], errors='coerce')
                
                # 转换为字典列表
                predictions = predictions_df.to_dict('records')
            
            # 生成基于预测结果的旅游推荐
            future_recommendations = []
            if predictions:
                # 加载景点数据
                data_dir = current_app.config['DATA_DIR']
                attractions_df = load_attractions_data(data_dir)
                
                for pred in predictions:
                    pred_date = pred['日期']
                    date_str = pred_date.strftime('%Y-%m-%d')
                    
                    # 获取当天的推荐景点
                    day_recommendations = []
                    if not attractions_df.empty:
                        # 根据天气条件筛选景点
                        filtered_attractions = attractions_df.copy()
                        
                        # 这里可以根据具体需求添加筛选逻辑
                        # 例如：根据温度、天气状况等推荐适合的景点类型
                        
                        # 取前3个景点作为推荐
                        top_attractions = filtered_attractions.head(3)
                        for _, attraction in top_attractions.iterrows():
                            day_recommendations.append({
                                '景点名称': attraction['景点名称'],
                                '景点类型': attraction['景点类型'],
                                '评分': attraction['评分'],
                                '简介': attraction['简介'],
                                '最佳季节': attraction['最佳季节'],
                                '门票价格': attraction['门票价格']
                            })
                    
                    future_recommendations.append({
                        'date': date_str,
                        'recommendations': day_recommendations
                    })
            
            # 将预测结果和推荐添加到收藏内容中
            content['predictions'] = predictions
            content['future_recommendations'] = future_recommendations
        except Exception as e:
            # 如果预测失败，添加错误信息
            content['error'] = f'预测执行失败: {str(e)}'
    
    return render_template('user/favorite_detail.html', favorite=favorite, content=content)
