import folium
from folium.plugins import MarkerCluster
from app.models import Attraction


class MapService:
    def __init__(self):
        pass
    
    def generate_travel_map(self, itinerary, start_city=None, target_city=None):
        """生成旅行路径的可视化地图
        - 当起点城市和目标城市相同时：生成闭环路径
        - 当起点城市和目标城市不同时：生成单向路径
        """
        # 创建地图，中心为辽宁省中心
        liaoning_center = [41.8057, 123.4315]  # 沈阳坐标
        m = folium.Map(location=liaoning_center, zoom_start=7, tiles='CartoDB positron')
        
        # 收集所有景点坐标
        all_coords = []
        
        # 城市中心点坐标数据
        city_coords = {
            '沈阳': [41.8057, 123.4315],
            '大连': [38.9140, 121.6147],
            '鞍山': [41.1182, 122.8907],
            '抚顺': [41.8645, 123.9506],
            '本溪': [41.3116, 123.7761],
            '丹东': [40.1374, 124.3426],
            '锦州': [41.1173, 121.1440],
            '营口': [40.6668, 122.1533],
            '阜新': [42.0053, 121.6148],
            '辽阳': [41.2641, 123.1753],
            '盘锦': [41.1243, 122.0730],
            '铁岭': [42.2901, 123.8398],
            '朝阳': [41.5732, 120.4790],
            '葫芦岛': [40.7315, 120.7610]
        }
        
        # 记录目标城市
        current_target_city = None
        
        # 当起点城市和目标城市不同时，添加起点城市中心点到路径
        if start_city and target_city and start_city != target_city:
            # 从城市坐标字典中获取起点城市中心点坐标
            start_city_key = start_city.replace("市", "")
            if start_city_key in city_coords:
                start_center = city_coords[start_city_key]
                # 添加起点城市中心点标记
                folium.Marker(
                    location=start_center,
                    popup=f"<h4>{start_city}中心</h4><p>城市: {start_city}</p><p>类型: 城市中心</p>",
                    tooltip=f"{start_city}中心",
                    icon=folium.Icon(
                        color='blue',
                        icon='home',  # 使用家图标表示起点
                        prefix='fa'
                    )
                ).add_to(m)
                # 将起点城市中心点添加到路径坐标列表的开头
                all_coords.append(start_center)
                print(f"添加{start_city}中心到路径，坐标: ({start_center[0]}, {start_center[1]})")
        
        # 添加每日行程标记
        for day, day_plan in enumerate(itinerary):
            day_color = ['blue', 'green', 'red', 'purple', 'orange', 'darkred'][day % 6]
            
            for i, attraction_info in enumerate(day_plan['attractions']):
                # 处理新的数据结构：attraction_info是包含attraction对象的字典
                if isinstance(attraction_info, dict) and 'attraction' in attraction_info:
                    attraction = attraction_info['attraction']
                else:
                    # 兼容旧的数据结构
                    attraction = attraction_info
                
                # 确保景点有有效的坐标
                if not attraction.latitude or not attraction.longitude:
                    print(f"景点 {attraction.name} 没有有效的坐标，跳过")
                    continue
                
                # 记录目标城市
                if not current_target_city:
                    current_target_city = attraction.city
                
                # 添加景点标记
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
                
                # 添加标记，使用简洁清晰的样式
                folium.Marker(
                    location=[attraction.latitude, attraction.longitude],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=attraction.name,  # 添加鼠标悬停提示
                    icon=folium.Icon(
                        color=day_color, 
                        icon='info-sign',  # 使用默认的信息标记图标
                        prefix='fa'
                    )
                ).add_to(m)
                
                # 添加到路径坐标列表
                all_coords.append([attraction.latitude, attraction.longitude])
                print(f"添加景点 {attraction.name} 到路径，坐标: ({attraction.latitude}, {attraction.longitude})")
        
        # 绘制路径
        print(f"总共有 {len(all_coords)} 个景点有有效的坐标")
        
        # 如果有有效的坐标，绘制路径
        if all_coords:
            # 只连接相邻的景点，不形成闭环，避免路径混乱
            path_coords = all_coords.copy()
            
            print(f"路径坐标列表长度: {len(path_coords)}")
            print(f"路径坐标: {path_coords}")
            
            # 添加路径线，确保至少有两个点
            if len(path_coords) >= 2:
                # 绘制从第一个景点到最后一个景点的单向路径，不形成闭环
                folium.PolyLine(
                    path_coords,
                    color='red',
                    weight=3,  # 适当的线条宽度
                    opacity=0.7,  # 适当的不透明度
                    tooltip='旅行路径',
                    dash_array=None  # 实线
                ).add_to(m)
                print("单向路径线已添加到地图")
            
            # 添加路径长度信息到地图中心
            path_length = self._calculate_path_length(path_coords)
            # 计算所有坐标的平均位置，将信息标记放在地图中心附近
            avg_lat = sum(coord[0] for coord in path_coords) / len(path_coords)
            avg_lon = sum(coord[1] for coord in path_coords) / len(path_coords)
            folium.Marker(
                location=[avg_lat, avg_lon],
                popup=f"<h5>路径信息</h5><p>总站点数: {len(all_coords)}个景点</p><p>总路径长度: {path_length:.2f}公里</p>",
                icon=folium.Icon(color='green', icon='info-circle', prefix='fa')
            ).add_to(m)
            
            # 如果有有效的坐标，将地图中心移动到这些坐标的平均位置，放大地图
            m.location = [avg_lat, avg_lon]
            m.zoom_start = 10
        else:
            # 如果没有有效的坐标，在地图中心添加提示标记
            # 尝试从目标城市获取坐标
            city_coords = {
                '沈阳': [41.8057, 123.4315],
                '大连': [38.9140, 121.6147],
                '鞍山': [41.1182, 122.8907],
                '抚顺': [41.8645, 123.9506],
                '本溪': [41.3116, 123.7761],
                '丹东': [40.1374, 124.3426],
                '锦州': [41.1173, 121.1440],
                '营口': [40.6668, 122.1533],
                '阜新': [42.0053, 121.6148],
                '辽阳': [41.2641, 123.1753],
                '盘锦': [41.1243, 122.0730],
                '铁岭': [42.2901, 123.8398],
                '朝阳': [41.5732, 120.4790],
                '葫芦岛': [40.7315, 120.7610]
            }
            
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
                        popup=f"<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息，无法显示路径。</p><p>目标城市: {city}</p>",
                        icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                    ).add_to(m)
                    print(f"使用目标城市 {city} 的坐标作为地图中心")
                else:
                    # 使用辽宁省中心作为地图中心
                    folium.Marker(
                        location=liaoning_center,  # 使用辽宁省中心
                        popup="<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息，无法显示路径。</p>",
                        icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                    ).add_to(m)
                    print("没有有效的坐标，添加了提示标记")
            else:
                # 使用辽宁省中心作为地图中心
                folium.Marker(
                    location=liaoning_center,  # 使用辽宁省中心
                    popup="<h5>提示</h5><p>当前行程中的景点没有有效的坐标信息，无法显示路径。</p>",
                    icon=folium.Icon(color='orange', icon='info-circle', prefix='fa')
                ).add_to(m)
                print("没有有效的坐标，添加了提示标记")
        
        # 添加辽宁省边界（如果有GeoJSON数据）
        self._add_liaoning_boundary(m)
        
        return m
    
    def _calculate_path_length(self, coords):
        """计算路径长度（公里）"""
        total_distance = 0
        
        for i in range(len(coords)-1):
            lat1, lon1 = coords[i]
            lat2, lon2 = coords[i+1]
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            total_distance += distance
        
        return total_distance
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """使用Haversine公式计算两个经纬度之间的距离（公里）"""
        import math
        
        # 地球半径（公里）
        R = 6371.0
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差异
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
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
        
        # 添加景点标记
        for attraction in attractions:
            if not attraction.latitude or not attraction.longitude:
                continue
            
            popup_html = f"<h4>{attraction.name}</h4>"
            popup_html += f"<p>城市: {attraction.city}</p>"
            popup_html += f"<p>类型: {attraction.type}</p>"
            popup_html += f"<p>评分: {attraction.rating if attraction.rating else '暂无评分'}</p>"
            
            folium.Marker(
                location=[attraction.latitude, attraction.longitude],
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
