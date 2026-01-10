import folium
from folium.plugins import MarkerCluster
from app.models import Attraction
import requests
import json
import math
import random


class MapService:
    def __init__(self):
        pass
    
    def generate_travel_map(self, itinerary, start_city=None, target_city=None):
        """生成旅行路径的可视化地图，支持多条不同路径的显示"""
        # 创建地图，中心为辽宁省中心
        liaoning_center = [41.8057, 123.4315]  # 沈阳坐标
        m = folium.Map(location=liaoning_center, zoom_start=7, tiles='CartoDB positron')
        
        # 城市中心点坐标数据 - 调整了近距离城市的坐标，避免圆弧形布局拥挤
        city_coords = {
            '沈阳': [41.8057, 123.4315],
            '大连': [38.9140, 121.6147],
            '鞍山': [41.1182, 122.8907],
            '抚顺': [41.9000, 124.0500],  # 调整：与沈阳和铁岭距离增加到约60公里
            '本溪': [41.3116, 123.7761],
            '丹东': [40.1374, 124.3426],
            '锦州': [41.1173, 121.1440],
            '营口': [40.6668, 122.1533],
            '阜新': [42.0053, 121.6148],
            '辽阳': [41.2000, 123.2500],  # 调整：与鞍山距离增加到约40公里
            '盘锦': [41.1243, 122.0730],
            '铁岭': [42.2901, 123.8398],
            '朝阳': [41.5732, 120.4790],
            '葫芦岛': [40.7315, 120.7610]
        }
        
        # 记录目标城市
        current_target_city = None
        
        # 添加每日行程标记
        # 跟踪已添加的坐标，确保每个标记都能显示在不同的位置
        added_coords = {}
        
        # 收集所有景点坐标，用于自动调整地图视图
        all_marker_coords = []
        
        # 创建一个统一的路径，包含所有景点
        all_attractions = []
        all_coords = []
        
        # 遍历所有行程，收集所有景点和坐标
        for day, day_plan in enumerate(itinerary):
            for i, attraction_info in enumerate(day_plan['attractions']):
                # 处理多种数据格式
                attraction = None
                
                # 格式1：attraction_info是包含attraction对象的字典
                if isinstance(attraction_info, dict) and 'attraction' in attraction_info:
                    attraction = attraction_info['attraction']
                # 格式2：attraction_info直接包含景点属性（来自前端序列化数据）
                elif isinstance(attraction_info, dict):
                    # 尝试从多种可能的字段名中获取坐标
                    lat = None
                    lon = None
                    
                    # 尝试不同的纬度字段名
                    for lat_key in ['latitude', 'lat', 'y', '纬度']:
                        if lat_key in attraction_info and attraction_info[lat_key] is not None and attraction_info[lat_key] != '':
                            try:
                                lat = float(attraction_info[lat_key])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # 尝试不同的经度字段名
                    for lon_key in ['longitude', 'lng', 'long', 'x', '经度']:
                        if lon_key in attraction_info and attraction_info[lon_key] is not None and attraction_info[lon_key] != '':
                            try:
                                lon = float(attraction_info[lon_key])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # 创建一个简单的景点对象，包含地图生成所需的基本信息
                    attraction = type('SimpleAttraction', (), {
                        'name': attraction_info.get('name', '未知景点'),
                        'city': attraction_info.get('city', '未知城市'),
                        'type': attraction_info.get('type', '未知类型'),
                        'rating': float(attraction_info.get('rating', 0.0)) if attraction_info.get('rating') else 0.0,
                        'latitude': lat,
                        'longitude': lon,
                        'description': attraction_info.get('description', ''),
                        'price': float(attraction_info.get('price', 0.0)) if attraction_info.get('price') else 0.0
                    })()
                # 格式3：attraction_info直接是attraction对象
                else:
                    attraction = attraction_info
                
                # 确保景点有有效的坐标（允许0.0值，因为可能是城市中心坐标）
                if attraction.latitude is None or attraction.longitude is None:
                    print(f"景点 {attraction.name} 没有有效的坐标，跳过")
                    continue
                
                # 辽宁省经纬度范围：放宽范围，确保所有有效的辽宁省景点坐标都能显示
                # 北纬38°-44°，东经118°-126°
                if not (38.0 <= attraction.latitude <= 44.0) or not (118.0 <= attraction.longitude <= 126.0):
                    print(f"景点 {attraction.name} 坐标超出辽宁省范围，跳过: ({attraction.latitude}, {attraction.longitude})")
                    continue
                
                # 记录目标城市
                if not current_target_city:
                    current_target_city = attraction.city
                
                # 为当前景点获取坐标
                original_lat = attraction.latitude
                original_lon = attraction.longitude
                coord_key = (original_lat, original_lon)
                
                # 用于显示标记的坐标（可能有偏移）
                display_lat = original_lat
                display_lon = original_lon
                
                # 检查是否已添加过相同坐标的标记
                if coord_key in added_coords:
                    # 如果已添加过，为新标记添加智能偏移，确保所有标记都能显示且不沿斜线分布
                    count = added_coords[coord_key]
                    # 使用圆形分布的偏移方式，避免沿斜线分布
                    angle = count * 0.5  # 每个标记间隔0.5弧度
                    distance = 0.001 * count  # 距离随标记数量增加而增加
                    
                    # 计算圆形偏移
                    display_lat = original_lat + math.sin(angle) * distance
                    display_lon = original_lon + math.cos(angle) * distance
                    
                    added_coords[coord_key] += 1
                    print(f"景点 {attraction.name} 坐标重复，添加圆形偏移: ({display_lat}, {display_lon})")
                else:
                    # 第一次添加该坐标
                    added_coords[coord_key] = 1
                
                # 添加景点标记，使用统一的蓝色
                popup_html = f"<h4>{attraction.name}</h4>"
                popup_html += f"<p>城市: {attraction.city}</p>"
                popup_html += f"<p>类型: {attraction.type}</p>"
                popup_html += f"<p>评分: {attraction.rating if attraction.rating else '暂无评分'}</p>"
                popup_html += f"<p>第{day+1}天 第{i+1}站</p>"
                
                # 添加推荐参观时间
                if isinstance(attraction_info, dict) and 'visit_time' in attraction_info:
                    popup_html += f"<p>推荐参观时间: {attraction_info['visit_time']}</p>"
                
                if day_plan.get('weather'):
                    popup_html += f"<p>天气: {day_plan['weather'].get('weather', '未知')}</p>"
                    popup_html += f"<p>温度: {day_plan['weather'].get('temperature', '未知')}°C</p>"
                
                # 添加标记，使用简洁清晰的样式，统一使用蓝色
                marker = folium.Marker(
                    location=[display_lat, display_lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=attraction.name,  # 添加鼠标悬停提示
                    icon=folium.Icon(
                        color='blue',  # 统一使用蓝色
                        icon='info-sign',  # 使用默认的信息标记图标
                        prefix='fa'
                    )
                )
                marker.add_to(m)
                print(f"成功添加景点标记: {attraction.name}，坐标: ({display_lat}, {display_lon})")
                
                # 保存用于调整地图视图的坐标
                all_marker_coords.append([display_lat, display_lon])
                
                # 将景点和坐标添加到统一列表
                all_attractions.append(attraction)
                all_coords.append([original_lat, original_lon])
        
        # 创建一个统一的路径
        paths = []
        if all_coords:
            path = {
                'name': '完整路径',
                'color': 'blue',  # 统一使用蓝色
                'attractions': all_attractions,
                'coords': all_coords
            }
            paths.append(path)
        
        # 绘制多条路径
        print(f"总共有 {len(paths)} 条路径需要绘制")
        
        # 为每条路径生成并绘制路径线
        for path in paths:
            if len(path['coords']) >= 2:
                # 生成当前路径的平滑曲线坐标
                path_line_coords = []
                
                # 遍历路径上的相邻景点，生成它们之间的曲线
                for i in range(len(path['coords']) - 1):
                    start_lat, start_lon = path['coords'][i]
                    end_lat, end_lon = path['coords'][i + 1]
                    
                    # 生成两个景点之间的曲线坐标
                    segment_coords = self._generate_smooth_path(start_lat, start_lon, end_lat, end_lon, path_index=paths.index(path))
                    
                    if i == 0:
                        # 第一段：添加所有坐标
                        path_line_coords.extend(segment_coords)
                    else:
                        # 后续段：跳过第一个坐标（避免重复）
                        path_line_coords.extend(segment_coords[1:])
                
                print(f"路径 '{path['name']}' 生成了 {len(path_line_coords)} 个坐标点")
                
                # 绘制当前路径线
                folium.PolyLine(
                    path_line_coords,
                    color=path['color'],
                    weight=4,  # 增加线条宽度，提高可见性
                    opacity=0.8,  # 提高不透明度，确保清晰可见
                    tooltip=path['name'],  # 显示路径名称
                    dash_array=None,  # 实线
                    smooth_factor=1.0,  # 平滑路径
                    z_index=1000  # 确保路径显示在最上层
                ).add_to(m)
                print(f"路径 '{path['name']}' 已添加到地图")
        
        # 自动调整地图视图，确保所有景点都能显示在视野内
        if all_marker_coords:
            # 计算所有标记坐标的边界
            min_lat = min(coord[0] for coord in all_marker_coords)
            max_lat = max(coord[0] for coord in all_marker_coords)
            min_lon = min(coord[1] for coord in all_marker_coords)
            max_lon = max(coord[1] for coord in all_marker_coords)
            
            # 调整边界，添加一些边距，确保所有内容都能清晰显示
            margin = 0.01  # 边距，单位为度
            m.fit_bounds([
                [min_lat - margin, min_lon - margin],  # 西南角
                [max_lat + margin, max_lon + margin]   # 东北角
            ])
            print(f"自动调整地图视图，边界: [{min_lat}, {min_lon}] 到 [{max_lat}, {max_lon}]")
        else:
            # 如果没有有效的坐标，在地图中心添加提示标记
            # 检查是否有目标城市的坐标
            city = target_city or current_target_city
            if city:
                # 去除城市名中的"市"后缀
                city = city.replace("市", "")
                if city in city_coords:
                    # 使用目标城市的坐标作为地图中心
                    m.location = city_coords[city]
                    m.zoom_start = 10
                    
                    # 在目标城市中心添加提示标记
                    folium.Marker(
                        location=city_coords[city],
                        popup=f"<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息。</p><p>目标城市: {city}</p>",
                        icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                    ).add_to(m)
                    print(f"使用目标城市 {city} 的坐标作为地图中心")
                else:
                    # 使用辽宁省中心作为地图中心
                    folium.Marker(
                        location=liaoning_center,  # 使用辽宁省中心
                        popup="<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息。</p>",
                        icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                    ).add_to(m)
                    print("没有有效的坐标，添加了提示标记")
            else:
                # 使用辽宁省中心作为地图中心
                folium.Marker(
                    location=liaoning_center,  # 使用辽宁省中心
                    popup="<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息。</p>",
                    icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                ).add_to(m)
                print("没有有效的坐标，添加了提示标记")
        
        # 添加辽宁省边界（如果有GeoJSON数据）
        self._add_liaoning_boundary(m)
        
        return m
    
    def _generate_smooth_path(self, start_lat, start_lon, end_lat, end_lon, path_index=0):
        """生成平滑的路径坐标，支持多条路径不重叠
        
        Args:
            start_lat: 起点纬度
            start_lon: 起点经度
            end_lat: 终点纬度
            end_lon: 终点经度
            path_index: 路径索引，用于生成不同的偏移，避免路径重叠
            
        Returns:
            list: 平滑路径的坐标点列表
        """
        # 计算起点和终点之间的距离和方向
        delta_lat = end_lat - start_lat
        delta_lon = end_lon - start_lon
        distance = math.sqrt(delta_lat ** 2 + delta_lon ** 2)
        
        # 如果距离为0，返回直线坐标
        if distance < 0.0001:
            return [[start_lat, start_lon], [end_lat, end_lon]]
        
        # 根据距离设置路径点数量，确保路径平滑且不过度复杂
        min_points = 15
        max_points = 150
        num_points = int(min(min_points + distance * 1000, max_points))
        
        # 生成路径点列表
        route_coords = []
        
        # 添加起点
        route_coords.append([start_lat, start_lon])
        
        # 移除固定的随机种子，让路径能够根据不同的景点组合动态生成不同的曲线
        # 使用当前时间作为基础，结合路径信息生成动态种子
        import time
        random.seed(int(time.time() * 1000) + path_index + len(route_coords))
        
        # 生成中间的路径点
        for i in range(1, num_points - 1):
            # 计算当前点的基本位置（沿直线）
            ratio = i / (num_points - 1)
            base_lat = start_lat + delta_lat * ratio
            base_lon = start_lon + delta_lon * ratio
            
            # 生成平滑的曲线偏移，使路径更自然流畅
            offset_factor = 0.02 + path_index * 0.01  # 减小偏移因子，使路径更平滑
            
            # 只使用一层低频正弦波，生成自然的弯曲
            # 降低频率和振幅，减少波浪形弯曲
            layer1_freq = 0.8  # 更低的频率，更少的弯曲
            layer1_amp = 0.8  # 更低的振幅，更小的弯曲幅度
            offset = offset_factor * layer1_amp * math.sin(ratio * math.pi * layer1_freq)
            
            # 计算垂直于路径方向的向量
            perpendicular_x = delta_lat  # 水平方向偏移
            perpendicular_y = -delta_lon  # 垂直方向偏移
            
            # 归一化垂直向量
            perpendicular_length = math.sqrt(perpendicular_x ** 2 + perpendicular_y ** 2)
            if perpendicular_length > 0:
                perpendicular_x /= perpendicular_length
                perpendicular_y /= perpendicular_length
            
            # 根据路径索引决定偏移方向，使不同路径向不同方向偏移
            direction = 1 if path_index % 2 == 0 else -1
            
            # 计算当前点的最终坐标
            current_lat = base_lat + perpendicular_y * offset * direction
            current_lon = base_lon + perpendicular_x * offset * direction
            
            route_coords.append([current_lat, current_lon])
        
        # 添加终点
        route_coords.append([end_lat, end_lon])
        
        return route_coords
    
    def _add_liaoning_boundary(self, m):
        """添加辽宁省边界"""
        import json
        import os
        
        # 查找辽宁GeoJSON文件
        geojson_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app', 'static', 'js', 'liaoning.json'
        )
        
        if os.path.exists(geojson_path):
            try:
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    liaoning_geojson = json.load(f)
                
                # 添加GeoJSON图层
                folium.GeoJson(
                    liaoning_geojson,
                    name='辽宁省边界',
                    style_function=lambda x: {
                        'fillColor': '#ffff00',
                        'color': '#000000',
                        'weight': 1,
                        'fillOpacity': 0.1
                    },
                    tooltip='辽宁省边界'
                ).add_to(m)
                
                # 添加图层控制器
                folium.LayerControl().add_to(m)
            except Exception as e:
                print(f"添加辽宁省边界失败: {e}")
    
    def generate_attraction_map(self, attractions):
        """生成景点分布地图"""
        # 创建地图，中心为辽宁省中心
        liaoning_center = [41.8057, 123.4315]  # 沈阳坐标
        m = folium.Map(location=liaoning_center, zoom_start=7, tiles='CartoDB positron')
        
        # 创建标记集群
        marker_cluster = MarkerCluster().add_to(m)
        
        # 跟踪已添加的坐标，确保每个标记都能显示在不同的位置
        added_coords = {}
        
        # 添加景点标记
        for attraction in attractions:
            if not attraction.latitude or not attraction.longitude:
                continue
            
            # 确保景点有有效的坐标（允许0.0值，因为可能是城市中心坐标）
            if attraction.latitude is None or attraction.longitude is None:
                print(f"景点 {attraction.name} 没有有效的坐标，跳过")
                continue
            
            # 辽宁省经纬度范围：放宽范围，确保所有有效的辽宁省景点坐标都能显示
            # 北纬38°-44°，东经118°-126°
            if not (38.0 <= attraction.latitude <= 44.0) or not (118.0 <= attraction.longitude <= 126.0):
                print(f"景点 {attraction.name} 坐标超出辽宁省范围，跳过: ({attraction.latitude}, {attraction.longitude})")
                continue
            
            # 为当前景点获取坐标
            original_lat = attraction.latitude
            original_lon = attraction.longitude
            coord_key = (original_lat, original_lon)
            
            # 用于显示标记的坐标（可能有偏移）
            display_lat = original_lat
            display_lon = original_lon
            
            # 检查是否已添加过相同坐标的标记
            if coord_key in added_coords:
                # 如果已添加过，为新标记添加智能偏移，确保所有标记都能显示且不沿斜线分布
                import math
                count = added_coords[coord_key]
                # 使用圆形分布的偏移方式，避免沿斜线分布
                angle = count * 0.5  # 每个标记间隔0.5弧度
                distance = 0.001 * count  # 距离随标记数量增加而增加
                
                # 计算圆形偏移
                display_lat = original_lat + math.sin(angle) * distance
                display_lon = original_lon + math.cos(angle) * distance
                
                added_coords[coord_key] += 1
                print(f"景点 {attraction.name} 坐标重复，添加圆形偏移: ({display_lat}, {display_lon})")
            else:
                # 第一次添加该坐标
                added_coords[coord_key] = 1
            
            popup_html = f"<h4>{attraction.name}</h4>"
            popup_html += f"<p>城市: {attraction.city}</p>"
            popup_html += f"<p>类型: {attraction.type}</p>"
            popup_html += f"<p>评分: {attraction.rating if attraction.rating else '暂无评分'}</p>"
            
            folium.Marker(
                location=[display_lat, display_lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(marker_cluster)
        
        # 添加辽宁省边界
        self._add_liaoning_boundary(m)
        
        return m
    
    def generate_weather_map(self, weather_data, attractions):
        """生成天气影响下的景点地图"""
        # 创建地图，中心为辽宁省中心
        liaoning_center = [41.8057, 123.4315]  # 沈阳坐标
        m = folium.Map(location=liaoning_center, zoom_start=7, tiles='CartoDB positron')
        
        # 添加天气信息标记
        for city, weather in weather_data.items():
            # 查找城市的代表景点作为位置
            city_attractions = [attr for attr in attractions if attr.city == city]
            if city_attractions:
                # 使用第一个景点的坐标
                attr = city_attractions[0]
                if attr.latitude and attr.longitude:
                    popup_html = f"<h4>{city}天气</h4>"
                    popup_html += f"<p>天气: {weather.get('weather', '未知')}</p>"
                    popup_html += f"<p>温度: {weather.get('temperature', '未知')}°C</p>"
                    popup_html += f"<p>风力: {weather.get('wind', '未知')}</p>"
                    
                    # 根据天气选择图标颜色
                    weather_color = self._get_weather_color(weather.get('weather', ''))
                    
                    folium.Marker(
                        location=[attr.latitude, attr.longitude],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color=weather_color, icon='cloud', prefix='fa')
                    ).add_to(m)
        
        # 添加辽宁省边界
        self._add_liaoning_boundary(m)
        
        return m
    
    def _get_weather_color(self, weather):
        """根据天气获取图标颜色"""
        weather = weather.lower()
        if '晴' in weather:
            return 'orange'
        elif '雨' in weather:
            return 'blue'
        elif '云' in weather or '阴' in weather:
            return 'gray'
        elif '雪' in weather:
            return 'lightblue'
        elif '雾' in weather or '霾' in weather:
            return 'beige'
        elif '雷' in weather:
            return 'darkpurple'
        else:
            return 'green'
