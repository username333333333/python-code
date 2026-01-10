from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService
from app.models import Itinerary, ItineraryDay, ItineraryAttraction, Attraction
from app import db
from datetime import datetime, timedelta

path_bp = Blueprint('path_optimization', __name__, url_prefix='/path')


@path_bp.route('/')
def index():
    """路径优化页面"""
    return render_template('simple_path_optimization.html')


@path_bp.route('/optimize', methods=['POST'])
@path_bp.route('/calculate', methods=['POST'])
def optimize_path():
    """优化旅行路径"""
    print("收到路径优化请求")
    
    try:
        data = request.get_json()
    except Exception as e:
        print(f"获取请求体失败: {str(e)}")
        data = {}
    
    try:
        start_city = data.get('start_city', '沈阳')
        days = int(data.get('days', 3))
        preferences = data.get('preferences', {})
        target_city = data.get('target_city', start_city)  # 目标城市默认为起点城市
        selected_attractions = data.get('selected_attractions', [])  # 获取用户选择的景点
        
        print(f"处理路径优化请求，参数: start_city={start_city}, days={days}, preferences={preferences}, target_city={target_city}, selected_attractions={len(selected_attractions)}")
        
        # 初始化服务
        path_service = PathOptimizationService()
        
        # 生成路径 - 传递用户选择的景点
        path_result = path_service.generate_closed_loop_path(
            start_city, days, preferences, target_city, selected_attractions
        )
        
        # 提取行程和预算
        itinerary = path_result['itinerary']
        budget = path_result['budget']
        
        # 转换为可序列化的格式
        serialized_itinerary = []
        for day_plan in itinerary:
            serialized_day = {
                'day': day_plan['day'],
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False),
                'risk_assessment': day_plan.get('risk_assessment', []),
                'recommended_hotels': day_plan.get('recommended_hotels', []),
                'recommended_dining': day_plan.get('recommended_dining', []),
                'attractions': [
                    {
                        'id': attr_info['attraction'].id if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.id,
                        'name': attr_info['attraction'].name if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.name,
                        'city': attr_info['attraction'].city if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.city,
                        'type': attr_info['attraction'].type if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.type,
                        'rating': attr_info['attraction'].rating if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.rating,
                        'price': attr_info['attraction'].price if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.price,
                        'duration': attr_info['attraction'].duration if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.duration,
                        'longitude': attr_info['attraction'].longitude if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.longitude,
                        'latitude': attr_info['attraction'].latitude if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.latitude,
                        'description': attr_info['attraction'].description if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info.description,
                        'visit_time': attr_info.get('visit_time'),
                        'travel_info': attr_info.get('travel_info')
                    } for attr_info in day_plan['attractions']
                ]
            }
            serialized_itinerary.append(serialized_day)
        
        # 检查行程是否为空
        is_empty = True
        for day_plan in serialized_itinerary:
            if day_plan['attractions']:
                is_empty = False
                break
        
        if is_empty:
            # 行程为空，返回明确的提示信息
            return jsonify({
                'success': False,
                'message': '未找到符合您偏好的景点，请尝试调整景点类型偏好或扩大搜索范围',
                'itinerary': [],
                'budget': {}
            })
        else:
            # 行程不为空，正常返回
            return jsonify({
                'success': True,
                'itinerary': serialized_itinerary,
                'budget': budget
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'路径优化失败: {str(e)}'
        }), 500


@path_bp.route('/adjust_for_weather', methods=['POST'])
def adjust_path_for_weather():
    """根据天气调整路径"""
    try:
        data = request.get_json()
        itinerary = data.get('itinerary')
        weather_forecast = data.get('weather_forecast')
        start_city = data.get('start_city')
        target_city = data.get('target_city')
        
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程数据不能为空'
            }), 400
        
        if not weather_forecast:
            return jsonify({
                'success': False,
                'message': '天气预报数据不能为空'
            }), 400
        
        # 初始化服务
        path_service = PathOptimizationService()
        map_service = MapService()
        
        # 从数据库获取景点对象
        from app.models import Attraction
        
        # 转换行程数据为包含景点对象的格式
        db_itinerary = []
        for day_plan in itinerary:
            # 获取景点对象
            attractions = []
            for attr_data in day_plan['attractions']:
                attr = None
                # 首先尝试通过id查找（兼容数据库id）
                if isinstance(attr_data['id'], int) or attr_data['id'].isdigit():
                    attr = Attraction.query.get(int(attr_data['id']))
                
                # 如果通过id找不到，尝试通过城市和名称查找
                if not attr and 'name' in attr_data and 'city' in attr_data:
                    attr = Attraction.query.filter_by(
                        name=attr_data['name'],
                        city=attr_data['city']
                    ).first()
                
                # 如果还是找不到，尝试从attr_data直接构建景点信息
                if not attr:
                    # 创建一个简单的景点对象，包含地图生成所需的基本信息
                    attr = type('SimpleAttraction', (), {
                        'name': attr_data.get('name', '未知景点'),
                        'city': attr_data.get('city', '未知城市'),
                        'type': attr_data.get('type', '未知类型'),
                        'rating': float(attr_data.get('rating', 0.0)),
                        'latitude': float(attr_data.get('latitude', 0.0)) if attr_data.get('latitude') else None,
                        'longitude': float(attr_data.get('longitude', 0.0)) if attr_data.get('longitude') else None
                    })()
                
                attractions.append(attr)
            
            db_itinerary.append({
                'day': day_plan['day'],
                'attractions': attractions,
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False)
            })
        
        # 优化路径
        adjusted_itinerary = path_service.optimize_path_for_weather(
            db_itinerary, weather_forecast
        )
        
        # 生成地图 - 传递正确的起点城市和目标城市
        map_object = map_service.generate_travel_map(adjusted_itinerary, start_city, target_city)
        
        # 转换为可序列化的格式
        serialized_itinerary = []
        for day_plan in adjusted_itinerary:
            serialized_day = {
                'day': day_plan['day'],
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False),
                'risk_assessment': day_plan.get('risk_assessment', []),
                'attractions': [
                    {
                        'id': attr.id,
                        'name': attr.name,
                        'city': attr.city,
                        'type': attr.type,
                        'rating': attr.rating,
                        'price': attr.price,
                        'duration': attr.duration,
                        'longitude': attr.longitude,
                        'latitude': attr.latitude,
                        'description': attr.description
                    } for attr in day_plan['attractions']
                ]
            }
            serialized_itinerary.append(serialized_day)
        
        return jsonify({
            'success': True,
            'adjusted_itinerary': serialized_itinerary,
            'map_html': map_object._repr_html_()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'天气调整失败: {str(e)}'
        }), 500


@path_bp.route('/generate_map', methods=['POST'])
def generate_map():
    """生成地图"""
    try:
        data = request.get_json()
        itinerary = data.get('itinerary')
        
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程数据不能为空'
            }), 400
        
        # 从数据库获取景点对象
        from app.models import Attraction
        
        # 转换行程数据为包含景点对象的格式
        db_itinerary = []
        for day_plan in itinerary:
            # 获取景点对象
            attractions = []
            for attr_data in day_plan['attractions']:
                attr = None
                
                # 尝试通过id查找（兼容数据库id）
                if isinstance(attr_data['id'], int) or attr_data['id'].isdigit():
                    attr = Attraction.query.get(int(attr_data['id']))
                
                # 如果通过id找不到，尝试通过城市和名称查找
                if not attr and 'name' in attr_data and 'city' in attr_data:
                    attr = Attraction.query.filter_by(
                        name=attr_data['name'],
                        city=attr_data['city']
                    ).first()
                
                # 如果还是找不到，尝试从attr_data直接构建景点信息
                if not attr:
                    # 从attr_data中提取经纬度，如果没有则使用默认值
                    lat = attr_data.get('latitude')
                    lon = attr_data.get('longitude')
                    
                    # 处理经纬度，确保是有效数字
                    try:
                        lat = float(lat) if lat not in [None, '', '，'] else None
                    except (ValueError, TypeError):
                        lat = None
                    
                    try:
                        lon = float(lon) if lon not in [None, '', '，'] else None
                    except (ValueError, TypeError):
                        lon = None
                    
                    # 创建一个简单的景点对象，包含地图生成所需的基本信息
                    attr = type('SimpleAttraction', (), {
                        'name': attr_data.get('name', '未知景点'),
                        'city': attr_data.get('city', '未知城市'),
                        'type': attr_data.get('type', '未知类型'),
                        'rating': float(attr_data.get('rating', 0.0)),
                        'latitude': lat,
                        'longitude': lon,
                        'description': attr_data.get('description', ''),
                        'price': float(attr_data.get('price', 0.0)) if attr_data.get('price') else 0.0
                    })()
                
                attractions.append(attr)
            
            db_itinerary.append({
                'day': day_plan['day'],
                'attractions': attractions,
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False)
            })
        
        # 初始化服务
        map_service = MapService()
        
        # 从行程中提取目标城市
        target_city = None
        if db_itinerary and db_itinerary[0]['attractions']:
            first_attr = db_itinerary[0]['attractions'][0]
            target_city = first_attr.city if hasattr(first_attr, 'city') else None
        
        # 从请求中获取start_city和target_city，如果没有则使用从行程中提取的target_city
        start_city = data.get('start_city', target_city)
        actual_target_city = data.get('target_city', target_city)
        
        # 生成地图 - 使用正确的起点城市和目标城市
        map_object = map_service.generate_travel_map(db_itinerary, start_city, actual_target_city)
        
        # 返回地图HTML
        return jsonify({
            'success': True,
            'map_html': map_object._repr_html_()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'地图生成失败: {str(e)}'
        }), 500


@path_bp.route('/save', methods=['POST'])
@login_required
def save_itinerary():
    """保存行程到数据库"""
    try:
        data = request.get_json()
        start_city = data.get('start_city')
        days = data.get('days')
        start_date = data.get('start_date')
        is_closed_loop = data.get('is_closed_loop', True)
        preferences = data.get('preferences', {})
        itinerary_data = data.get('itinerary')
        
        if not all([start_city, days, start_date, itinerary_data]):
            return jsonify({
                'success': False,
                'message': '缺少必要的行程数据'
            }), 400
        
        # 创建行程主记录
        itinerary = Itinerary(
            user_id=current_user.id,
            days=days,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            start_city=start_city,
            is_closed_loop=is_closed_loop,
            preferences=preferences,
            status='active'
        )
        db.session.add(itinerary)
        db.session.flush()  # 获取itinerary.id
        
        # 保存每日行程
        for day_plan in itinerary_data:
            day_number = day_plan['day']
            itinerary_day = ItineraryDay(
                itinerary_id=itinerary.id,
                day_number=day_number,
                date=datetime.strptime(start_date, '%Y-%m-%d').date() + timedelta(days=day_number-1),
                weather=str(day_plan.get('weather', ''))
            )
            db.session.add(itinerary_day)
            db.session.flush()  # 获取itinerary_day.id
            
            # 保存每个景点
            for order, attr_data in enumerate(day_plan['attractions']):
                attraction_id = attr_data['id']
                itinerary_attraction = ItineraryAttraction(
                    itinerary_day_id=itinerary_day.id,
                    attraction_id=attraction_id,
                    order=order
                )
                db.session.add(itinerary_attraction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '行程保存成功',
            'itinerary_id': itinerary.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'行程保存失败: {str(e)}'
        }), 500


@path_bp.route('/history', methods=['GET'])
@login_required
def get_history_itineraries():
    """获取历史行程列表"""
    try:
        # 获取当前用户的所有行程
        itineraries = Itinerary.query.filter_by(user_id=current_user.id).order_by(Itinerary.created_at.desc()).all()
        
        # 转换为可序列化的格式
        result = []
        for itinerary in itineraries:
            result.append({
                'id': itinerary.id,
                'start_city': itinerary.start_city,
                'days': itinerary.days,
                'start_date': itinerary.start_date.strftime('%Y-%m-%d'),
                'is_closed_loop': itinerary.is_closed_loop,
                'status': itinerary.status,
                'created_at': itinerary.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'itineraries': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史行程失败: {str(e)}'
        }), 500


@path_bp.route('/history/<int:itinerary_id>', methods=['GET'])
@login_required
def get_itinerary(itinerary_id):
    """获取特定行程详情"""
    try:
        # 获取行程
        itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=current_user.id).first()
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程不存在或无权访问'
            }), 404
        
        # 构建行程数据
        itinerary_data = []
        itinerary_days = ItineraryDay.query.filter_by(itinerary_id=itinerary.id).order_by(ItineraryDay.day_number).all()
        
        for itinerary_day in itinerary_days:
            # 获取当日景点
            itinerary_attractions = ItineraryAttraction.query.filter_by(itinerary_day_id=itinerary_day.id).order_by(ItineraryAttraction.order).all()
            
            # 构建景点数据
            attractions = []
            for itinerary_attr in itinerary_attractions:
                attraction = Attraction.query.get(itinerary_attr.attraction_id)
                if attraction:
                    attractions.append({
                        'id': attraction.id,
                        'name': attraction.name,
                        'city': attraction.city,
                        'type': attraction.type,
                        'rating': attraction.rating,
                        'price': attraction.price,
                        'duration': attraction.duration,
                        'longitude': attraction.longitude,
                        'latitude': attraction.latitude,
                        'description': attraction.description
                    })
            
            itinerary_data.append({
                'day': itinerary_day.day_number,
                'weather': itinerary_day.weather,
                'attractions': attractions
            })
        
        return jsonify({
            'success': True,
            'itinerary': itinerary_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取行程详情失败: {str(e)}'
        }), 500


@path_bp.route('/history/<int:itinerary_id>', methods=['DELETE'])
@login_required
def delete_itinerary(itinerary_id):
    """删除行程"""
    try:
        # 获取行程
        itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=current_user.id).first()
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程不存在或无权访问'
            }), 404
        
        # 删除行程（级联删除ItineraryDay和ItineraryAttraction）
        db.session.delete(itinerary)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '行程删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除行程失败: {str(e)}'
        }), 500
