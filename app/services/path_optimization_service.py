import networkx as nx
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.models import Attraction
from app import db
from app.services.traffic_prediction_service import TrafficPredictionService, TrafficPredictionServiceFactory
from app.services.weather_service import WeatherService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.recommendation_service import RecommendationService
from app.services.accommodation_dining_service import AccommodationDiningService


class PathOptimizationService:
    def __init__(self):
        # 延迟初始化，只在需要时构建图
        self.graph = None
        # 只获取必要的景点数据，不存储所有景点
        self.attraction_dict = {}  # 空字典，在需要时动态填充
        # 初始化客流量预测服务，但延迟训练
        self.traffic_service = None
        self.traffic_models_trained = False
        # 初始化天气服务
        self.weather_service = None
        # 初始化风险评估服务
        self.risk_service = None
        # 初始化推荐服务
        self.recommendation_service = None
        # 初始化住宿餐饮服务
        self.accommodation_dining_service = None
        
        # 城市中心点坐标数据
        self.city_coords = {
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
        
        # 初始化时调用延迟初始化方法
        self._init_traffic_service()
        self._init_weather_service()
        self._init_risk_service()
        self._init_recommendation_service()
        self._init_accommodation_dining_service()
    
    def _build_attraction_graph(self):
        """构建景点图模型，只在需要时调用"""
        if self.graph is not None:
            return self.graph
        
        G = nx.Graph()
        
        # 简化图构建，只添加必要的节点，不添加边
        # 边将在需要时动态计算
        attractions = Attraction.query.all()
        
        # 添加景点节点
        for attraction in attractions:
            if attraction.latitude and attraction.longitude:
                G.add_node(attraction.id, 
                          name=attraction.name,
                          city=attraction.city,
                          type=attraction.type,
                          rating=attraction.rating,
                          latitude=attraction.latitude,
                          longitude=attraction.longitude)
        
        # 不再预计算所有边，边将在需要时动态计算
        
        self.graph = G
        return G
    
    def _create_city_center_attraction(self, city):
        """创建一个模拟的景点对象，用于表示城市中心点
        
        Args:
            city: 城市名称
            
        Returns:
            模拟的景点对象，具有与Attraction模型相同的属性
        """
        class MockAttraction:
            """模拟景点类，用于表示城市中心点"""
            def __init__(self, city, coords):
                self.id = 0  # 特殊ID，表示城市中心点
                self.name = f"{city}中心"
                self.city = city
                self.type = "城市中心"
                self.description = f"{city}的中心点"
                self.rating = None
                self.price = 0.0
                self.duration = "0小时"
                self.longitude = coords[1]
                self.latitude = coords[0]
                self.phone = None
                self.best_season = "全年"
                
            def __repr__(self):
                return f'<MockAttraction {self.name}>'
        
        # 获取城市坐标
        city = city.replace("市", "")  # 去除城市名中的"市"后缀
        coords = self.city_coords.get(city, [0, 0])
        
        # 创建并返回模拟景点对象
        return MockAttraction(city, coords)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两个经纬度之间的距离，使用Haversine公式"""
        # 检查是否有None值
        if None in [lat1, lon1, lat2, lon2]:
            return float('inf')  # 返回无穷大表示不可达
        
        # Haversine公式
        # 将角度转换为弧度
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 计算差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        # 地球半径（公里）
        r = 6371.0
        
        # 计算距离
        distance = r * c
        
        return distance
    
    def _filter_attractions(self, preferences, start_city, target_city):
        """根据用户偏好筛选景点，只包含目标城市的景点，并结合推荐服务"""
        # 直接使用目标城市作为筛选条件，不考虑用户提供的cities偏好
        # 移除城市名称中的"市"后缀，确保与数据库中的格式一致
        target_city_query = target_city.replace("市", "")
        
        # 只查询目标城市的景点
        query = Attraction.query.filter(Attraction.city == target_city_query)
        
        # 根据评分筛选
        min_rating = preferences.get('min_rating', 0)
        if min_rating > 0:
            query = query.filter(Attraction.rating >= min_rating)
        
        # 获取所有满足基本条件的景点
        attractions = query.all()
        print(f"_filter_attractions返回景点数量: {len(attractions)}")
        
        # 如果没有景点，直接返回
        if not attractions:
            return attractions
        
        # 使用推荐服务对景点进行排序和筛选
        if self.recommendation_service:
            # 获取景点类型偏好
            attraction_types = preferences.get('attraction_types', [])
            
            # 如果有景点类型偏好，使用推荐服务获取更精准的推荐
            if attraction_types and len(attraction_types) > 0:
                try:
                    # 类型映射：处理用户选择的类型与数据库实际类型的匹配
                    type_mapping = {
                        '风景区': ['风景区', '风景名胜'],
                        '风景名胜': ['风景区', '风景名胜'],
                        '公园': ['公园', '城市公园', '生态公园'],
                        '博物馆': ['博物馆', '博物院', '陈列馆', '纪念馆'],
                        '历史古迹': ['历史古迹', '古迹', '古建筑', '历史建筑', '遗址', '古迹遗址'],
                        '自然景观': ['自然景观', '自然', '山水', '湖泊', '河流', '森林', '山脉'],
                        '科教文化服务': ['博物馆', '博物院', '陈列馆', '纪念馆', '科教文化服务'],
                        '体育休闲服务': ['体育', '休闲', '运动', '体育休闲服务']
                    }
                    
                    # 获取要匹配的所有类型列表
                    all_target_types = []
                    for selected_type in attraction_types:
                        target_types = type_mapping.get(selected_type, [selected_type])
                        all_target_types.extend(target_types)
                    # 去重
                    all_target_types = list(set(all_target_types))
                    
                    # 扩展匹配逻辑：不仅匹配类型字段，还匹配名称和描述
                    filtered_by_type = []
                    for attr in attractions:
                        # 检查景点类型是否在目标类型列表中
                        match = False
                        
                        # 匹配景点类型字段
                        if attr.type in all_target_types:
                            match = True
                        # 匹配景点名称
                        elif any(keyword in attr.name for keyword in all_target_types):
                            match = True
                        # 匹配景点描述
                        elif attr.description and any(keyword in attr.description for keyword in all_target_types):
                            match = True
                        # 特殊类型的关键词匹配
                        elif '博物馆' in attraction_types and '博物馆' in attr.name:
                            match = True
                        elif '公园' in attraction_types and ('公园' in attr.name or '园' in attr.name):
                            match = True
                        elif '风景区' in attraction_types and ('风景区' in attr.name or '风景' in attr.name):
                            match = True
                        elif '历史古迹' in attraction_types and ('古迹' in attr.name or '遗址' in attr.name or '古' in attr.name or '历史' in attr.name):
                            match = True
                        elif '自然景观' in attraction_types and ('自然' in attr.name or '山水' in attr.name or '湖' in attr.name or '河' in attr.name or '山' in attr.name):
                            match = True
                        
                        if match:
                            filtered_by_type.append(attr)
                    
                    print(f"根据类型{all_target_types}过滤后景点数量: {len(filtered_by_type)}")
                    
                    # 如果过滤后没有景点，直接返回空列表
                    if not filtered_by_type:
                        print("没有找到符合类型条件的景点，返回空列表")
                        return []
                    
                    # 使用推荐服务根据景点类型排序
                    # 传递处理后的城市名称（去除"市"后缀）
                    # 使用最相关的类型进行推荐（用户选择的第一个类型）
                    recommended_df = self.recommendation_service.recommend_by_attraction_type(
                        attraction_type=attraction_types[0],
                        city=target_city_query,
                        top_n=len(filtered_by_type),
                        min_rating=min_rating
                    )
                    
                    print(f"推荐服务返回结果数量: {len(recommended_df)}")
                    
                    if not recommended_df.empty:
                        # 根据推荐结果重新排序景点列表
                        recommended_names = recommended_df['景点名称'].tolist()
                        
                        # 按推荐顺序排序景点
                        sorted_attractions = []
                        seen = set()
                        
                        # 先添加推荐的景点
                        for name in recommended_names:
                            for attr in filtered_by_type:
                                # 确保attr是景点对象，而不是字典
                                if hasattr(attr, 'id') and hasattr(attr, 'name'):
                                    if attr.name == name and attr.id not in seen:
                                        sorted_attractions.append(attr)
                                        seen.add(attr.id)
                                        break
                        
                        # 再添加未被推荐的景点
                        for attr in filtered_by_type:
                            # 确保attr是景点对象，而不是字典
                            if hasattr(attr, 'id'):
                                if attr.id not in seen:
                                    sorted_attractions.append(attr)
                                    seen.add(attr.id)
                        
                        # 只有在排序后的景点列表不为空时才使用排序结果
                        if sorted_attractions:
                            attractions = sorted_attractions
                            print(f"排序后景点数量: {len(attractions)}")
                    else:
                        # 如果推荐服务没有返回结果，使用过滤后的景点列表
                        attractions = filtered_by_type
                        print(f"使用过滤后的景点列表，数量: {len(attractions)}")
                except Exception as e:
                    # 如果推荐服务出现任何错误，使用原始的景点列表
                    print(f"推荐服务出现错误: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        return attractions
    
    def _generate_initial_population(self, attractions, start_city, target_city, population_size=20):
        """生成初始种群，路径结构：目标城市景点（行程生成时会自动添加起点和终点）"""
        population = []
        
        # 确保attractions不为空
        if not attractions:
            return population
        
        for _ in range(population_size):
            # 生成随机路径长度（目标城市景点数量）
            # 确保路径长度不超过可用景点数量，且至少为1
            max_path_length = len(attractions)
            path_length = random.randint(1, min(7, max_path_length))
            
            # 随机选择目标城市的景点
            # 如果可用景点数量不足，允许重复选择
            if len(attractions) >= path_length:
                selected_target_attrs = random.sample(attractions, path_length)
            else:
                # 当景点数量不足时，重复使用现有景点
                selected_target_attrs = []
                for _ in range(path_length):
                    selected_target_attrs.append(random.choice(attractions))
            
            # 构建路径：只包含目标城市景点，行程生成时会自动添加起点和终点
            path = selected_target_attrs
            
            population.append(path)
        
        return population
    
    def _fitness(self, path, weather_forecast=None, day_index=None, target_city=None):
        """计算路径的适应度，考虑距离、评分、客流量、天气因素和目标城市"""
        if len(path) < 2:
            return 0
        
        total_distance = 0
        total_rating = 0
        target_city_score = 0  # 目标城市得分
        total_traffic_score = 0  # 客流量得分
        
        # 计算总距离、总评分
        for i in range(len(path)-1):
            attr1 = path[i]
            attr2 = path[i+1]
              
              
            # 跳过None值和非景点对象
            if attr1 is None or attr2 is None:
                continue
            
            # 确保attr1和attr2是景点对象，而不是字典
            if not hasattr(attr1, 'latitude') or not hasattr(attr2, 'latitude'):
                print(f"警告：跳过非景点对象: attr1={type(attr1)}, attr2={type(attr2)}")
                continue
            
            # 直接使用距离计算，不再依赖图的边，提高性能
            distance = self._calculate_distance(
                attr1.latitude, attr1.longitude,
                attr2.latitude, attr2.longitude
            )
            
            total_distance += distance
            total_rating += attr1.rating if attr1.rating else 0
            
            # 计算目标城市得分：经过目标城市的景点越多，得分越高
            if target_city and attr1.city == target_city:
                target_city_score += 1
        
        # 归一化处理
        rating_score = total_rating / len(path) if path else 0
        distance_score = 1 / (total_distance + 1)  # 距离越短，分数越高
        
        # 目标城市得分：经过目标城市的景点比例
        target_city_ratio = target_city_score / len(path) if path else 0
        
        # 计算客流量得分（避免拥挤）
        if self.traffic_service and path:
            for attr in path:
                try:
                    # 跳过None值
                    if attr is None:
                        continue
                        
                    # 使用默认天气数据，简化计算
                    # 准备一个简单的天气数据，包含模型需要的所有特征
                    import pandas as pd
                    import numpy as np
                    from datetime import datetime
                    
                    # 获取当前日期信息
                    today = datetime.now()
                    
                    # 创建一个简单的天气数据DataFrame
                    weather_df = pd.DataFrame({
                        '最高气温': [25],
                        '最低气温': [15],
                        '平均气温': [20],
                        '降水量': [0],
                        '风力(白天)_数值': [3],
                        '月份': [today.month],
                        '星期': [today.weekday()],
                        '是否周末': [1 if today.weekday() >= 5 else 0],
                        '是否节假日': [0],
                        '极端天气': [0]
                    })
                    
                    # 获取预测客流量
                    traffic_result = self.traffic_service.predict_traffic(
                        attr.name, 
                        weather_df,  # 传递DataFrame而不是字典
                        False
                    )
                    
                    # 处理返回的元组
                    traffic = traffic_result[0] if isinstance(traffic_result, tuple) else traffic_result
                    
                    if traffic is not None and traffic > 0:
                        # 客流量越低，得分越高（避免拥挤）
                        # 假设正常客流量为5000人，超过10000人视为拥挤
                        if traffic < 5000:
                            traffic_score = 1.0
                        elif traffic < 10000:
                            traffic_score = 0.5
                        else:
                            traffic_score = 0.1
                        total_traffic_score += traffic_score
                except Exception as e:
                    # 遇到错误时跳过该景点的客流量计算，避免影响整体性能
                    print(f"客流量计算错误: {str(e)}")
                    # 继续使用默认得分
                    total_traffic_score += 0.8
                    continue
        
        # 归一化客流量得分
        traffic_score = total_traffic_score / len(path) if path else 0
        
        # 加权计算最终适应度，包含客流量因素
        # 权重：评分(0.3) + 距离(0.3) + 目标城市(0.2) + 客流量(0.2)
        fitness = rating_score * 0.3 + distance_score * 0.3 + target_city_ratio * 0.2 + traffic_score * 0.2
        
        return fitness
    
    def _fitness_simple(self, path, target_city=None):
        """简化的适应度计算方法，跳过客流量计算，提高性能"""
        if len(path) < 2:
            return 0
        
        total_distance = 0
        total_rating = 0
        target_city_score = 0  # 目标城市得分
        
        # 计算总距离、总评分
        for i in range(len(path)-1):
            attr1 = path[i]
            attr2 = path[i+1]
            
            # 跳过None值和非景点对象
            if attr1 is None or attr2 is None:
                continue
            
            # 确保attr1和attr2是景点对象，而不是字典
            if not hasattr(attr1, 'latitude') or not hasattr(attr2, 'latitude'):
                print(f"警告：跳过非景点对象: attr1={type(attr1)}, attr2={type(attr2)}")
                continue
            
            # 直接使用距离计算，不再依赖图的边，提高性能
            distance = self._calculate_distance(
                attr1.latitude, attr1.longitude,
                attr2.latitude, attr2.longitude
            )
            
            total_distance += distance
            total_rating += attr1.rating if attr1.rating else 0
            
            # 计算目标城市得分：经过目标城市的景点越多，得分越高
            if target_city and attr1.city == target_city:
                target_city_score += 1
        
        # 归一化处理
        rating_score = total_rating / len(path) if path else 0
        distance_score = 1 / (total_distance + 1)  # 距离越短，分数越高
        
        # 目标城市得分：经过目标城市的景点比例
        target_city_ratio = target_city_score / len(path) if path else 0
        
        # 简化的适应度计算，不包含客流量因素
        # 权重：评分(0.5) + 距离(0.3) + 目标城市(0.2)
        fitness = rating_score * 0.5 + distance_score * 0.3 + target_city_ratio * 0.2
        
        return fitness
    
    def _init_traffic_service(self):
        """延迟初始化客流量预测服务"""
        if not self.traffic_service:
            self.traffic_service = TrafficPredictionServiceFactory.create_service(
                service_type="sklearn",
                data_dir="data"
            )
            # 跳过模型训练，直接使用预测服务，避免训练时间过长
            self.traffic_models_trained = True
            print("客流量预测服务初始化，跳过模型训练")
    
    def _init_weather_service(self):
        """初始化天气服务"""
        if not self.weather_service:
            try:
                self.weather_service = WeatherService(
                    data_dir="data",
                    city_name="沈阳"  # 默认城市，后续可以根据需要动态设置
                )
                print("天气服务初始化成功")
            except Exception as e:
                print(f"天气服务初始化失败: {str(e)}")
                self.weather_service = None
    
    def _init_risk_service(self):
        """初始化风险评估服务"""
        if not self.risk_service:
            try:
                self.risk_service = RiskAssessmentService(
                    data_dir="data"
                )
                print("风险评估服务初始化成功")
            except Exception as e:
                print(f"风险评估服务初始化失败: {str(e)}")
                self.risk_service = None
    
    def _init_recommendation_service(self):
        """初始化推荐服务"""
        if not self.recommendation_service:
            try:
                self.recommendation_service = RecommendationService(
                    data_dir="data"
                )
                print("推荐服务初始化成功")
            except Exception as e:
                print(f"推荐服务初始化失败: {str(e)}")
                self.recommendation_service = None
    
    def _init_accommodation_dining_service(self):
        """初始化住宿餐饮服务"""
        if not self.accommodation_dining_service:
            try:
                self.accommodation_dining_service = AccommodationDiningService(
                    data_dir="data"
                )
                print("住宿餐饮服务初始化成功")
            except Exception as e:
                print(f"住宿餐饮服务初始化失败: {str(e)}")
                self.accommodation_dining_service = None
    
    def _crossover(self, parent1, parent2):
        """顺序交叉(OX)，用于生成新的路径个体"""
        if len(parent1) < 3 or len(parent2) < 3:
            return parent1.copy(), parent2.copy()
        
        # 选择交叉点
        start = random.randint(1, len(parent1) - 2)
        end = random.randint(start + 1, len(parent1) - 1)
        
        # 创建后代
        child1 = [None] * len(parent1)
        child2 = [None] * len(parent2)
        
        # 复制中间段
        child1[start:end] = parent1[start:end]
        child2[start:end] = parent2[start:end]
        
        # 填充剩余位置
        def fill_child(child, parent, start, end):
            position = end
            for gene in parent:
                if gene not in child:
                    if position >= len(child):
                        position = 0
                    child[position] = gene
                    position += 1
        
        fill_child(child1, parent2, start, end)
        fill_child(child2, parent1, start, end)
        
        return child1, child2
    
    def _mutate(self, path, mutation_rate=0.1):
        """交换变异，随机交换路径中的两个景点"""
        if len(path) < 2:
            return path
        
        if random.random() < mutation_rate:
            # 选择两个不同的位置
            idx1, idx2 = random.sample(range(len(path)), 2)
            # 交换景点
            path[idx1], path[idx2] = path[idx2], path[idx1]
        
        return path
    
    def _genetic_algorithm(self, population, days, generations=8, mutation_rate=0.1, weather_forecast=None, day_index=None, target_city=None):
        """遗传算法优化路径，包含交叉和变异操作"""
        # 如果种群为空，直接返回空列表
        if not population:
            return []
        
        population_size = len(population)
        
        for generation in range(generations):
            # 计算适应度
            fitness_scores = []
            for path in population:
                # 简化适应度计算，跳过客流量计算以提高性能
                score = self._fitness_simple(path, target_city)
                fitness_scores.append((score, path))
            
            # 按适应度排序
            fitness_scores.sort(reverse=True, key=lambda x: x[0])
            
            # 选择最佳个体保留到下一代（精英保留）
            elite_size = max(1, population_size // 10)  # 保留10%的精英
            elite = [path for _, path in fitness_scores[:elite_size]]
            
            # 创建新一代
            new_population = elite.copy()
            
            # 生成剩余个体
            while len(new_population) < population_size:
                # 选择父母，使用轮盘赌选择，简化选择逻辑
                parent1 = random.choices(population, weights=[score for score, _ in fitness_scores], k=1)[0]
                parent2 = random.choices(population, weights=[score for score, _ in fitness_scores], k=1)[0]
                
                # 交叉生成后代
                child1, child2 = self._crossover(parent1, parent2)
                
                # 变异
                child1 = self._mutate(child1, mutation_rate)
                child2 = self._mutate(child2, mutation_rate)
                
                # 添加到新一代
                new_population.append(child1)
                if len(new_population) < population_size:
                    new_population.append(child2)
            
            # 只保留前population_size个个体
            population = new_population[:population_size]
        
        # 返回最佳路径，只使用简化适应度计算以提高性能
        best_path = max(population, key=lambda x: self._fitness_simple(x, target_city))
        return best_path
    
    def _ensure_closed_loop(self, path, start_city):
        """确保路径是闭环的，起点和终点相同，使用目标城市的景点"""
        if path and path[0] != path[-1]:
            # 直接使用起点作为终点，形成闭环
            path.append(path[0])
        return path
    
    def _calculate_travel_info(self, prev_attr, curr_attr):
        """计算两个景点之间的出行时间和推荐交通方式"""
        if not prev_attr or not curr_attr:
            return {
                'travel_time': '0分钟',
                'transportation': '步行',
                'distance': '0公里'
            }
        
        # 计算距离
        distance = self._calculate_distance(
            prev_attr.latitude, prev_attr.longitude,
            curr_attr.latitude, curr_attr.longitude
        )
        
        # 推荐交通方式和计算出行时间
        if distance < 2:
            # 短距离：步行
            travel_time = round(distance * 15)  # 步行速度：4公里/小时
            transportation = '步行'
        elif distance < 10:
            # 中等距离：公交或共享单车
            travel_time = round(distance * 5 + 10)  # 公交：12公里/小时，加上10分钟等待时间
            transportation = '公交/共享单车'
        else:
            # 长距离：打车或地铁
            travel_time = round(distance * 2 + 15)  # 打车：30公里/小时，加上15分钟等待时间
            transportation = '打车/地铁'
        
        return {
            'travel_time': f'{travel_time}分钟',
            'transportation': transportation,
            'distance': f'{distance:.1f}公里'
        }
    
    def _generate_itinerary(self, path, days, start_city, target_city, selected_attractions=None):
        """生成详细行程安排，确保每天都有推荐景点：
        1. 每天都包含目标城市景点
        2. 当起点城市和目标城市相同时，包含完整的闭环路径
        3. 当起点城市和目标城市不同时，只包含目标城市的景点，不自动添加起点城市的景点
        4. 只有当用户明确添加了某个城市的景点时，该城市的景点才会出现在行程计划中
        5. 为每个景点添加风险评估信息
        6. 为每个景点添加出行时间和交通方式参考
        """
        itinerary = []
        
        # 确保路径结构正确
        if len(path) < 1:
            # 如果路径太短，直接返回
            return [{
                'day': 1,
                'attractions': [],
                'weather': None,
                'adjusted': False,
                'risk_assessment': []
            }]
        
        # 分离路径中的不同部分
        if start_city == target_city:
            # 当起点城市和目标城市相同时，确保路径是闭环的
            if path[0] != path[-1]:
                path.append(path[0])
            
            target_attrs = path[1:-1]  # 中间的目标城市景点
        else:
            # 当起点城市和目标城市不同时，只使用目标城市的景点，不包含城市中心点
            target_attrs = path
            
            # 检查路径的第一个元素是否是城市中心点（通过id=0判断）
            if target_attrs and hasattr(target_attrs[0], 'id') and target_attrs[0].id == 0:
                # 如果第一个元素是城市中心点，将其移除，只保留目标城市景点
                target_attrs = target_attrs[1:]  # 移除城市中心点，只保留目标城市景点
        
        # 确保至少有足够的目标城市景点分配到每天
        # 如果目标景点数量不足，复制一些景点以确保每天都有
        if len(target_attrs) < days:
            # 复制景点以确保每天至少有一个
            while len(target_attrs) < days:
                target_attrs.extend(target_attrs[:days - len(target_attrs)])
        
        # 计算每天应该访问的目标城市景点数量
        # 调整：每天都包含目标城市景点
        daily_target_attrs = max(1, len(target_attrs) // days)  # 每天至少1个景点
        
        # 分配目标城市景点到每天
        current_idx = 0
        for day in range(days):
            # 创建当天的景点列表
            day_attractions = []
            
            # 分配目标城市景点
            if day == days - 1:
                # 最后一天：添加所有剩余的目标城市景点
                day_target_attrs = target_attrs[current_idx:]
                day_attractions.extend(day_target_attrs)
            else:
                # 其他天：分配固定数量的目标城市景点
                day_target_attrs = target_attrs[current_idx:current_idx + daily_target_attrs]
                day_attractions.extend(day_target_attrs)
                # 更新索引
                current_idx += len(day_target_attrs)
            
            # 为当天的景点添加出行时间和交通方式
            detailed_attractions = []
            for i, attr in enumerate(day_attractions):
                attraction_info = {
                    'attraction': attr,
                    'visit_time': f'09:00 + {i * 2}小时',  # 推荐参观时间，每2小时一个景点
                    'travel_info': None
                }
                
                if i > 0:
                    # 计算与前一个景点的出行信息
                    prev_attr = day_attractions[i-1]
                    travel_info = self._calculate_travel_info(prev_attr, attr)
                    attraction_info['travel_info'] = travel_info
                
                detailed_attractions.append(attraction_info)
            
            # 创建当天的行程
            day_plan = {
                'day': day + 1,
                'attractions': detailed_attractions,
                'weather': None,  # 后续会填充
                'adjusted': False,
                'risk_assessment': []
            }
            
            itinerary.append(day_plan)
        
        return itinerary
    
    def generate_closed_loop_path(self, start_city, days, preferences, target_city=None, selected_attractions=None):
        """生成旅行路径，结构：
        - 当起点城市和目标城市相同时：起点城市 → 目标城市景点 → 起点城市（闭环）
        - 当起点城市和目标城市不同时：起点城市 → 目标城市景点（单向路径）
        """
        print(f"开始生成路径，起点城市: {start_city}, 目标城市: {target_city}, 天数: {days}, selected_attractions: {len(selected_attractions) if selected_attractions else 0}")
        
        # 目标城市默认为起点城市（纯闭环）
        if not target_city:
            target_city = start_city
            print(f"目标城市未指定，使用起点城市: {target_city}")
        
        try:
            # 获取起点城市的景点（用于起点和终点）
            start_city_query = start_city + "市" if "市" not in start_city else start_city
            print(f"查询起点城市景点，查询条件: {start_city_query}")
            start_attractions = Attraction.query.filter(Attraction.city == start_city_query).limit(5).all()
            print(f"找到起点城市景点数量: {len(start_attractions)}")
            
            # 验证起点城市景点
            valid_start_attractions = []
            for attr in start_attractions:
                if hasattr(attr, 'id'):
                    valid_start_attractions.append(attr)
                else:
                    print(f"警告：起点城市景点中包含非景点对象: {type(attr)}")
            start_attractions = valid_start_attractions
            
            if not start_attractions:
                print("没有找到起点城市的景点，使用第一个景点作为起点和终点")
                first_attr = Attraction.query.first()
                if first_attr and hasattr(first_attr, 'id'):
                    start_attractions = [first_attr]
                else:
                    print("没有找到任何景点，无法生成路径")
                    return {'itinerary': [{"day": 1, "attractions": [], "weather": None, "adjusted": False}], 'budget': {}}
            
            if not start_attractions:
                print("没有找到任何景点，无法生成路径")
                return {'itinerary': [{"day": 1, "attractions": [], "weather": None, "adjusted": False}], 'budget': {}}
            
            # 1. 优先使用用户选择的景点
            suitable_attractions = []
            if selected_attractions and len(selected_attractions) > 0:
                print(f"使用用户选择的景点，数量: {len(selected_attractions)}")
                # 从用户选择的景点中获取景点名称和城市，然后从数据库中查询对应的景点对象
                for selected_attr in selected_attractions:
                    attr_name = selected_attr.get('name')
                    attr_city = selected_attr.get('city')
                    if attr_name and attr_city:
                        # 查询对应的景点对象，移除城市名称中的"市"后缀，确保与数据库中的格式一致
                        attr_city_query = attr_city.replace("市", "")
                        # 先尝试精确匹配
                        attr = Attraction.query.filter(
                            Attraction.name == attr_name,
                            Attraction.city == attr_city_query
                        ).first()
                        if attr:
                            suitable_attractions.append(attr)
                        else:
                            # 如果精确匹配失败，尝试模糊匹配景点名称
                            print(f"尝试精确匹配未找到对应景点: {attr_city} - {attr_name}")
                            attr = Attraction.query.filter(
                                Attraction.name.like(f"%{attr_name}%"),
                                Attraction.city == attr_city_query
                            ).first()
                            if attr:
                                suitable_attractions.append(attr)
                                print(f"模糊匹配找到对应景点: {attr.city} - {attr.name}")
                            else:
                                print(f"模糊匹配也未找到对应景点: {attr_city} - {attr_name}")
                print(f"从用户选择的景点中找到数据库对象数量: {len(suitable_attractions)}")
            else:
                # 2. 如果没有用户选择的景点，根据偏好筛选目标城市的景点
                print(f"开始筛选目标城市景点，目标城市: {target_city}")
                suitable_attractions = self._filter_attractions(preferences, start_city, target_city)
                print(f"根据偏好筛选后景点数量: {len(suitable_attractions)}")
            
            # 验证适合的景点
            valid_suitable_attractions = []
            for attr in suitable_attractions:
                if hasattr(attr, 'id'):
                    valid_suitable_attractions.append(attr)
                else:
                    print(f"警告：适合的景点中包含非景点对象: {type(attr)}")
            suitable_attractions = valid_suitable_attractions
            
            # 如果没有符合条件的景点，返回空行程
            if not suitable_attractions:
                print("没有找到符合条件的景点，返回空行程")
                return {'itinerary': [{"day": 1, "attractions": [], "weather": None, "adjusted": False}], 'budget': {}}
            
            # 确保景点列表不重复
            unique_attractions = []
            seen = set()
            for attr in suitable_attractions:
                attr_key = f"{attr.city}-{attr.name}"
                if attr_key not in seen:
                    seen.add(attr_key)
                    unique_attractions.append(attr)
            suitable_attractions = unique_attractions
            print(f"去重后景点数量: {len(suitable_attractions)}")
            
            # 如果使用用户选择的景点，不再额外添加其他景点
            if selected_attractions and len(selected_attractions) > 0:
                # 如果用户选择的景点数量不足，重复使用现有景点，而不是添加新景点
                if len(suitable_attractions) < 2:
                    print(f"用户选择的景点数量不足2个，重复使用现有景点，当前数量: {len(suitable_attractions)}")
                    suitable_attractions = suitable_attractions * 2
                    print(f"重复后景点数量: {len(suitable_attractions)}")
                
                # 确保景点数量至少等于旅行天数，这样每天至少有一个景点
                if len(suitable_attractions) < days:
                    print(f"用户选择的景点数量({len(suitable_attractions)})小于旅行天数({days})，重复使用现有景点")
                    # 重复景点直到数量至少等于旅行天数
                    while len(suitable_attractions) < days:
                        suitable_attractions.extend(suitable_attractions)
                    # 限制最大数量，避免过多重复
                    suitable_attractions = suitable_attractions[:days * 2]
                    print(f"重复后景点数量: {len(suitable_attractions)}")
            else:
                # 限制景点数量，提高性能
                suitable_attractions = suitable_attractions[:50]  # 最多使用50个景点
                print(f"限制景点数量后: {len(suitable_attractions)}")
            
            # 确保suitable_attractions不为空
            if not suitable_attractions:
                # 如果没有任何景点，返回空行程
                print("没有找到任何景点，无法生成路径")
                return {'itinerary': [{"day": 1, "attractions": [], "weather": None, "adjusted": False}], 'budget': {}}
            
            # 确保suitable_attractions至少有2个元素
            if len(suitable_attractions) < 2:
                # 如果只有1个景点，复制一份
                print(f"景点数量不足2个，复制景点，当前数量: {len(suitable_attractions)}")
                suitable_attractions = suitable_attractions * 2
                print(f"复制后景点数量: {len(suitable_attractions)}")
            
            # 2. 构建初始种群，包含跨城市的完整路径结构
            print("开始构建初始种群")
            initial_population = []
            population_size = 20
            
            # 过滤掉可能包含的None值
            valid_attractions = [attr for attr in suitable_attractions if attr is not None and hasattr(attr, 'id')]
            print(f"有效景点数量: {len(valid_attractions)}")
            
            for _ in range(population_size):
                # 生成随机路径长度（目标城市景点数量）
                # 确保路径长度不超过可用景点数量，且至少为1
                max_path_length = len(valid_attractions)
                path_length = random.randint(1, min(7, max_path_length))
                
                # 随机选择目标城市的景点
                # 如果可用景点数量不足，允许重复选择
                selected_target_attrs = []
                if len(valid_attractions) >= path_length:
                    selected_target_attrs = random.sample(valid_attractions, path_length)
                else:
                    # 当景点数量不足时，重复使用现有景点
                    for _ in range(path_length):
                        selected_target_attrs.append(random.choice(valid_attractions))
                
                # 构建路径：目标城市景点（遗传算法优化后，行程生成时会自动添加起点和终点）
                path = selected_target_attrs
                initial_population.append(path)
            print(f"初始种群构建完成，种群大小: {len(initial_population)}")
            
            # 3. 遗传算法优化，传递目标城市参数
            print("开始遗传算法优化")
            optimized_path = self._genetic_algorithm(initial_population, days, target_city=target_city)
            print(f"遗传算法优化完成，优化后路径长度: {len(optimized_path)}")
            
            # 确保optimized_path中的所有元素都是景点对象
            validated_path = []
            for item in optimized_path:
                if hasattr(item, 'id'):  # 检查是否为景点对象
                    validated_path.append(item)
                else:
                    print(f"警告：跳过非景点对象: {type(item)}, 内容: {item}")
            optimized_path = validated_path
            print(f"验证后路径长度: {len(optimized_path)}")
            
            # 如果遗传算法返回空列表，直接使用suitable_attractions中的景点构建路径
            if not optimized_path:
                print("遗传算法返回空路径，使用随机景点构建路径")
                # 随机选择3-7个景点
                path_length = random.randint(3, min(7, len(suitable_attractions)))
                optimized_path = random.sample(suitable_attractions, path_length)
                print(f"随机构建路径长度: {len(optimized_path)}")
            
            # 4. 构建最终路径
            print("开始构建最终路径")
            final_path = []
            
            # 根据起点城市和目标城市是否相同，构建不同类型的路径
            if start_city == target_city:
                # 当起点城市和目标城市相同时，构建闭环路径
                print("构建闭环路径")
                
                # 确保路径有足够的景点
                if optimized_path:
                    # 路径：起点城市景点 → 目标城市景点 → 起点城市景点
                    final_path = [optimized_path[0]] + optimized_path + [optimized_path[0]]
                else:
                    # 如果没有优化路径，使用随机景点构建闭环
                    random_attr = random.choice(suitable_attractions)
                    final_path = [random_attr, random_attr]
            else:
                # 当起点城市和目标城市不同时，构建单向路径
                print("构建单向路径")
                
                # 使用城市中心点作为起点位置，而不是具体景点
                start_attr = self._create_city_center_attraction(start_city)
                print(f"使用{start_city}的中心点作为起点")
                
                # 路径：城市中心点 → 目标城市景点
                final_path = [start_attr] + optimized_path
            
            print(f"最终路径构建完成，路径长度: {len(final_path)}")
            
            # 确保最终路径中的所有元素都是景点对象
            valid_final_path = []
            for item in final_path:
                if hasattr(item, 'id'):  # 检查是否为景点对象
                    valid_final_path.append(item)
                else:
                    print(f"警告：最终路径中包含非景点对象: {type(item)}")
            final_path = valid_final_path
            print(f"验证后最终路径长度: {len(final_path)}")
            
            # 确保最终路径长度至少为 2
            if len(final_path) < 2:
                print("最终路径长度不足，添加额外景点")
                # 从合适的景点中随机选择一个添加到路径中
                random_attr = random.choice(suitable_attractions)
                final_path.append(random_attr)
                print(f"添加额外景点后，最终路径长度: {len(final_path)}")
            
            # 5. 生成详细行程安排，包含从起点城市到目标城市的完整闭环路径
            print("开始生成详细行程安排")
            itinerary = self._generate_itinerary(final_path, days, start_city, target_city, selected_attractions)
            print(f"行程安排生成完成，天数: {len(itinerary)}")
            
            # 6. 自动获取未来天气预报并进行天气敏感型路径优化
            # 如果使用用户选择的景点，跳过天气优化，避免添加新景点
            if self.weather_service and not selected_attractions:
                try:
                    # 获取未来天气预测
                    print(f"开始获取未来天气预报，城市: {target_city}, 天数: {days}")
                    weather_forecast = self.weather_service.get_future_weather_forecast(
                        days=days,
                        city=target_city
                    )
                    print(f"获取天气预报完成，预报天数: {len(weather_forecast)}")
                    
                    if weather_forecast:
                        # 根据天气预测优化路径
                        print("开始根据天气预测优化路径")
                        itinerary = self.optimize_path_for_weather(itinerary, weather_forecast)
                        print(f"成功根据天气预测优化路径，共优化{len(itinerary)}天行程")
                except Exception as e:
                    print(f"天气优化失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 添加酒店和餐饮推荐
            print("开始添加酒店和餐饮推荐")
            itinerary_with_accommodation_dining = self._add_accommodation_dining_recommendations(
                itinerary, target_city
            )
            print(f"酒店和餐饮推荐添加完成")
            
            # 计算旅行费用预算
            print("开始计算旅行费用预算")
            budget = self.calculate_travel_budget(
                target_city, days, preferences, start_city
            )
            print(f"旅行费用预算计算完成: {budget}")
            
            print("路径生成完成")
            return {
                'itinerary': itinerary_with_accommodation_dining,
                'budget': budget,
                'start_city': start_city,
                'target_city': target_city
            }
        except Exception as e:
            print(f"路径生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'itinerary': [{"day": 1, "attractions": [], "weather": None, "adjusted": False}],
                'budget': {}
            }
    
    def optimize_path_for_weather(self, itinerary, weather_forecast):
        """根据天气预测优化路径，包括过滤不适合的景点和添加替代景点"""
        optimized_itinerary = []
        
        # 获取目标城市（从第一天行程的第一个景点获取）
        target_city = None
        if itinerary and itinerary[0].get('attractions') and itinerary[0]['attractions']:
            first_attr_info = itinerary[0]['attractions'][0]
            # 处理新的数据结构：attraction_info是包含attraction对象的字典
            if isinstance(first_attr_info, dict) and 'attraction' in first_attr_info:
                first_attr = first_attr_info['attraction']
            else:
                # 兼容旧的数据结构
                first_attr = first_attr_info
            target_city = first_attr.city.split('市')[0]  # 去除"市"后缀
        
        for day, day_plan in enumerate(itinerary):
            try:
                # 获取当日天气（如果有）
                day_weather = None
                if day < len(weather_forecast):
                    day_weather = weather_forecast[day]
                
                # 复制原始行程
                new_day_plan = day_plan.copy()
                new_day_plan['risk_assessment'] = []  # 初始化风险评估列表
                
                if day_weather and target_city:
                    # 获取原始景点列表
                    original_attractions = day_plan['attractions']
                    
                    # 提取原始景点对象
                    raw_attractions = []
                    for attr_info in original_attractions:
                        if isinstance(attr_info, dict) and 'attraction' in attr_info:
                            raw_attractions.append(attr_info['attraction'])
                        else:
                            raw_attractions.append(attr_info)
                    
                    # 调用新的天气调整逻辑，包括过滤和替换
                    adjusted_raw_attractions = self._adjust_attractions_for_weather(
                        raw_attractions, day_weather, target_city
                    )
                    
                    # 处理最后一天的返回点
                    if day == len(itinerary) - 1 and adjusted_raw_attractions:
                        # 获取起点城市（第一个景点的城市）
                        start_city = None
                        if itinerary[0].get('attractions') and itinerary[0]['attractions']:
                            first_attr_info = itinerary[0]['attractions'][0]
                            if isinstance(first_attr_info, dict) and 'attraction' in first_attr_info:
                                start_city = first_attr_info['attraction'].city
                            else:
                                start_city = first_attr_info.city
                        
                        if start_city:
                            last_attr = adjusted_raw_attractions[-1]
                            if last_attr.city != start_city:
                                # 查找起点城市的景点并添加到末尾
                                start_attrs = Attraction.query.filter(
                                    Attraction.city == start_city
                                ).limit(1).all()
                                if start_attrs:
                                    adjusted_raw_attractions.append(start_attrs[0])
                    
                    # 重新构建详细的景点信息列表，保留visit_time和travel_info
                    adjusted_attractions = []
                    for i, attr in enumerate(adjusted_raw_attractions):
                        # 尝试从原始列表中获取对应的详细信息
                        attr_info = {
                            'attraction': attr,
                            'visit_time': f'09:00 + {i * 2}小时',  # 默认推荐参观时间
                            'travel_info': None
                        }
                        
                        # 如果原始列表中有对应的详细信息，复用其travel_info
                        if i < len(original_attractions) and i > 0:
                            original_attr_info = original_attractions[i]
                            if isinstance(original_attr_info, dict) and 'travel_info' in original_attr_info:
                                # 计算与前一个景点的出行信息
                                if i > 0:
                                    prev_attr = adjusted_raw_attractions[i-1]
                                    travel_info = self._calculate_travel_info(prev_attr, attr)
                                    attr_info['travel_info'] = travel_info
                        
                        adjusted_attractions.append(attr_info)
                    
                    new_day_plan['attractions'] = adjusted_attractions
                    new_day_plan['weather'] = day_weather
                    new_day_plan['adjusted'] = adjusted_raw_attractions != raw_attractions
                    
                    # 添加风险评估
                    if self.risk_service:
                        # 准备天气数据格式，转换为风险评估服务所需的格式
                        risk_weather = {
                            'weather': day_weather.get('weather', ''),
                            'temperature': day_weather.get('temperature', 0),
                            'wind': day_weather.get('wind', 0)
                        }
                        
                        # 为每个景点评估风险
                        risk_assessments = []
                        for attr_info in adjusted_attractions:
                            # 获取景点对象
                            attraction = attr_info['attraction'] if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info
                            
                            # 获取景点类型
                            attraction_type = attraction.type
                            
                            # 评估风险
                            risk_result = self.risk_service.assess_risk(attraction_type, risk_weather)
                            
                            # 保存风险评估结果
                            risk_assessments.append({
                                'attraction_id': attraction.id,
                                'attraction_name': attraction.name,
                                'risk_level': risk_result['risk_level'],
                                'advice': risk_result['advice'],
                                'weather_factors': risk_result['weather_factors']
                            })
                        
                        new_day_plan['risk_assessment'] = risk_assessments
                
                optimized_itinerary.append(new_day_plan)
            except Exception as e:
                # 如果当天的天气调整失败，使用原始行程
                print(f"第{day+1}天天气调整失败: {str(e)}")
                import traceback
                traceback.print_exc()
                optimized_itinerary.append(day_plan.copy())
        
        return optimized_itinerary
    
    def _evaluate_weather_suitability(self, attraction, weather):
        """评估景点在特定天气下的适合度"""
        if not weather:
            return 1.0  # 没有天气信息，默认为适合
        
        # 获取天气信息
        weather_desc = weather.get('weather', '').lower()
        
        # 详细的景点类型分类
        indoor_keywords = ['博物馆', '纪念馆', '科技馆', '美术馆', '展览馆', '室内', '故居', '陈列馆', '文化创意园', '民俗馆', '艺术馆']
        outdoor_keywords = ['公园', '山', '峰', '岭', '谷', '洞', '瀑布', '森林', '草原', '自然保护区', '风景区']
        beach_keywords = ['海滨', '沙滩', '海岛', '海岸', '海景', '海滩']
        outdoor_activities = ['游乐场', '主题公园', '动物园', '植物园']
        
        attr_type = attraction.type.lower()
        attr_name = attraction.name.lower()
        
        # 分类景点
        is_indoor = any(keyword in attr_type or keyword in attr_name for keyword in indoor_keywords)
        is_beach = any(keyword in attr_type or keyword in attr_name for keyword in beach_keywords)
        is_outdoor_activity = any(keyword in attr_type or keyword in attr_name for keyword in outdoor_activities)
        is_outdoor = not is_indoor and not is_beach and not is_outdoor_activity
        
        # 评估适合度
        # 1.0 = 非常适合, 0.5 = 一般适合, 0.0 = 不适合
        
        # 雨天情况
        if any(rain in weather_desc for rain in ['雨', '小雨', '中雨', '大雨', '暴雨', '雷阵雨']):
            if is_indoor:
                return 1.0  # 室内景点非常适合雨天
            elif is_beach:
                return 0.0  # 海滩景点不适合雨天
            elif is_outdoor_activity:
                return 0.2  # 室外活动场所不太适合雨天
            else:
                return 0.3  # 其他室外景点不太适合雨天
        
        # 雪天情况
        elif any(snow in weather_desc for snow in ['雪', '小雪', '中雪', '大雪', '暴雪']):
            if is_indoor:
                return 1.0  # 室内景点非常适合雪天
            elif is_beach:
                return 0.0  # 海滩景点不适合雪天
            elif is_outdoor_activity:
                return 0.3  # 室外活动场所不太适合雪天
            else:
                return 0.4  # 其他室外景点不太适合雪天
        
        # 晴天情况
        elif any(sun in weather_desc for sun in ['晴', '晴朗', '多云']):
            if is_indoor:
                return 0.8  # 室内景点适合晴天，但不如室外景点适合
            elif is_beach or is_outdoor_activity:
                return 1.0  # 海滩和室外活动场所非常适合晴天
            else:
                return 0.9  # 其他室外景点非常适合晴天
        
        # 其他天气情况
        else:
            return 0.7  # 默认适合度
    
    def _add_accommodation_dining_recommendations(self, itinerary, target_city):
        """为行程添加酒店和餐饮推荐"""
        if not self.accommodation_dining_service:
            print("住宿餐饮服务未初始化，无法添加推荐")
            return itinerary
        
        # 为每天行程添加推荐
        for day_plan in itinerary:
            # 只添加目标城市的推荐
            if day_plan.get('attractions'):
                # 推荐酒店（第一天添加即可）
                if day_plan['day'] == 1:
                    hotels = self.accommodation_dining_service.recommend_hotels(
                        city=target_city,
                        top_n=3
                    )
                    day_plan['recommended_hotels'] = hotels
                
                # 为每天添加餐饮推荐
                dining = self.accommodation_dining_service.recommend_dining(
                    city=target_city,
                    top_n=3
                )
                day_plan['recommended_dining'] = dining
        
        return itinerary
    
    def _calculate_city_distance(self, city1, city2):
        """计算两个城市之间的距离（公里）"""
        # 辽宁省主要城市坐标（纬度，经度）
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
        
        # 检查城市是否在坐标列表中
        if city1 not in city_coords or city2 not in city_coords:
            return 0
        
        # 使用Haversine公式计算距离
        import math
        lat1, lon1 = city_coords[city1]
        lat2, lon2 = city_coords[city2]
        
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
        
        # 地球半径（公里）
        r = 6371.0
        
        # 计算距离
        distance = r * c
        
        return distance
    
    def calculate_travel_budget(self, city, days, preferences, start_city=None):
        """计算旅行费用预算"""
        if not self.accommodation_dining_service:
            print("住宿餐饮服务未初始化，无法计算预算")
            return {}
        
        # 默认预算参数
        hotel_type = preferences.get('hotel_type', '经济型酒店')
        dining_type = preferences.get('dining_type', '中餐')
        meals_per_day = preferences.get('meals_per_day', 3)
        
        # 优先使用传入的start_city参数，其次从preferences中获取，最后使用city作为默认值
        if start_city is None:
            start_city = preferences.get('start_city', city)  # 获取出发城市
        
        # 计算各项费用
        accommodation_cost = self.accommodation_dining_service.calculate_accommodation_cost(
            city, days, hotel_type
        )
        
        dining_cost = self.accommodation_dining_service.calculate_dining_cost(
            city, days, meals_per_day, dining_type
        )
        
        # 估算门票费用（假设每个景点平均50元）
        ticket_cost = days * 3 * 50  # 每天3个景点，每个50元
        
        # 计算城市间交通费用
        city_transport_cost = 0
        city_distance = 0
        
        if start_city != city:  # 只有当出发城市和目标城市不同时，才计算交通费用
            city_distance = self._calculate_city_distance(start_city, city)
            if city_distance > 0:
                # 根据距离计算交通费用：0.5元/公里
                city_transport_cost = round(city_distance * 0.5, 2)
        
        # 估算市内交通费用（每天）
        local_transport_cost = days * 100  # 每天100元
        transport_cost = city_transport_cost + local_transport_cost
        
        # 估算其他费用
        other_cost = days * 50  # 每天50元
        
        # 总费用
        total_cost = accommodation_cost + dining_cost + ticket_cost + transport_cost + other_cost
        
        budget = {
            'total_cost': round(total_cost, 2),
            'breakdown': {
                '住宿费用': round(accommodation_cost, 2),
                '餐饮费用': round(dining_cost, 2),
                '门票费用': ticket_cost,
                '交通费用': round(transport_cost, 2),
                '城市间交通费用': round(city_transport_cost, 2),
                '市内交通费用': round(local_transport_cost, 2),
                '其他费用': other_cost
            },
            'suggestions': [
                f"住宿推荐：{hotel_type}，预计每晚{round(accommodation_cost/days, 2)}元",
                f"餐饮推荐：{dining_type}，预计每人每天{round(dining_cost/days, 2)}元",
                f"城市间交通：{start_city}到{city}，距离{round(city_distance, 1)}公里，预计费用{round(city_transport_cost, 2)}元",
                "建议携带现金或信用卡，以备不时之需",
                "可根据实际情况调整预算"
            ]
        }
        
        return budget
    
    def _filter_attractions_by_weather(self, attractions, weather):
        """根据天气过滤不适合的景点"""
        if not weather:
            return attractions
        
        suitable_attractions = []
        
        for attr in attractions:
            suitability = self._evaluate_weather_suitability(attr, weather)
            if suitability > 0.3:  # 只保留适合度大于0.3的景点
                suitable_attractions.append(attr)
        
        return suitable_attractions
    
    def _get_suitable_replacements(self, current_attractions, weather, target_city, count=3):
        """获取适合当前天气的替代景点"""
        # 获取目标城市的所有景点
        # 移除城市名称中的"市"后缀，确保与数据库中的格式一致
        target_city_query = target_city.replace("市", "")
        all_attractions = Attraction.query.filter(Attraction.city == target_city_query).all()
        
        # 计算每个景点的适合度并排序
        scored_attractions = []
        for attr in all_attractions:
            # 跳过已经在当前行程中的景点
            if attr in current_attractions:
                continue
            
            suitability = self._evaluate_weather_suitability(attr, weather)
            if suitability > 0.5:  # 只考虑适合度较高的景点
                scored_attractions.append((suitability, attr))
        
        # 按适合度排序，取前count个
        scored_attractions.sort(reverse=True, key=lambda x: x[0])
        replacements = [attr for _, attr in scored_attractions[:count]]
        
        return replacements
    
    def _adjust_attractions_for_weather(self, attractions, weather, target_city):
        """根据天气调整景点，包括过滤和替换"""
        if not weather:
            return attractions
        
        # 1. 过滤不适合的景点
        filtered_attractions = self._filter_attractions_by_weather(attractions, weather)
        
        # 2. 如果过滤后景点不足，添加适合的替代景点
        original_count = len(attractions)
        if len(filtered_attractions) < original_count:
            # 获取需要补充的数量
            needed = original_count - len(filtered_attractions)
            # 获取适合的替代景点
            replacements = self._get_suitable_replacements(filtered_attractions, weather, target_city, needed)
            # 添加替代景点
            filtered_attractions.extend(replacements)
        
        # 3. 根据适合度排序
        scored_attractions = [(self._evaluate_weather_suitability(attr, weather), attr) for attr in filtered_attractions]
        scored_attractions.sort(reverse=True, key=lambda x: x[0])
        sorted_attractions = [attr for _, attr in scored_attractions]
        
        # 4. 限制数量，保持与原列表相同长度
        return sorted_attractions[:original_count]
    
    def _optimize_return_path(self, attractions, start_city, weather):
        """优化最后一天的返回路径，简化逻辑，提高性能"""
        if not attractions:
            return attractions
        
        # 直接返回，不再使用复杂的优化算法，大幅提高速度
        # 仅确保最后一个景点是起点城市的景点
        if attractions[-1].city != start_city:
            # 查找所有起点城市的景点，使用数据库查询替代self.attractions
            start_attrs = Attraction.query.filter(
                Attraction.city == start_city
            ).limit(1).all()
            if start_attrs:
                # 选择第一个起点城市景点作为返回点，不进行距离计算
                attractions.append(start_attrs[0])
        
        return attractions
    
    def get_attraction_by_id(self, attraction_id):
        """根据ID获取景点信息"""
        return self.attraction_dict.get(attraction_id)
