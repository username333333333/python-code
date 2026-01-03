import pandas as pd
import os
from pathlib import Path
import random

class AccommodationDiningService:
    """酒店和餐饮推荐服务"""
    
    def __init__(self, data_dir):
        """初始化服务，加载所有城市的酒店和餐饮数据"""
        self.data_dir = Path(data_dir)
        self.itinerary_dir = self.data_dir / "itinerary"
        
        # 初始化价格区间（用于预算计算）- 移到前面，确保在加载数据前可用
        self.price_ranges = {
            'hotel': {
                '经济型酒店': (100, 300),
                '商务酒店': (300, 600),
                '豪华酒店': (600, 1500),
                '民宿': (200, 500),
                '度假酒店': (500, 1200),
                '青年旅舍': (50, 150),
                '温泉酒店': (400, 1000)
            },
            'dining': {
                '中餐': (50, 150),
                '火锅': (80, 200),
                '快餐': (20, 50),
                '烧烤': (60, 180),
                '西餐': (100, 300),
                '海鲜': (150, 400)
            }
        }
        
        if not self.itinerary_dir.exists():
            raise FileNotFoundError(f"行程数据目录不存在: {self.itinerary_dir}")
        
        # 加载所有城市的酒店和餐饮数据
        self.hotels_data = self._load_all_accommodation_data()
        self.dining_data = self._load_all_dining_data()
    
    def _load_all_accommodation_data(self):
        """加载所有城市的酒店数据"""
        hotels = []
        hotel_files = list(self.itinerary_dir.glob("*_hotel.csv"))
        
        for file_path in hotel_files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                # 为酒店添加价格信息
                df['价格区间'] = df['类型'].apply(lambda x: self.price_ranges['hotel'].get(x, (200, 500)))
                df['平均价格'] = df['价格区间'].apply(lambda x: sum(x) / 2)
                hotels.append(df)
            except Exception as e:
                print(f"加载酒店文件 {file_path} 失败: {e}")
        
        if not hotels:
            return pd.DataFrame()
        
        return pd.concat(hotels, ignore_index=True)
    
    def _load_all_dining_data(self):
        """加载所有城市的餐饮数据"""
        dining = []
        dining_files = list(self.itinerary_dir.glob("*_catering.csv"))
        
        for file_path in dining_files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                # 为餐饮添加价格信息
                df['价格区间'] = df['类型'].apply(lambda x: self.price_ranges['dining'].get(x, (50, 150)))
                df['人均价格'] = df['价格区间'].apply(lambda x: sum(x) / 2)
                dining.append(df)
            except Exception as e:
                print(f"加载餐饮文件 {file_path} 失败: {e}")
        
        if not dining:
            return pd.DataFrame()
        
        return pd.concat(dining, ignore_index=True)
    
    def recommend_hotels(self, city, hotel_type=None, budget=None, top_n=3):
        """推荐酒店"""
        if self.hotels_data.empty:
            return []
        
        # 筛选城市
        city_hotels = self.hotels_data[self.hotels_data['城市'] == city]
        
        if city_hotels.empty:
            return []
        
        # 筛选酒店类型
        if hotel_type:
            city_hotels = city_hotels[city_hotels['类型'] == hotel_type]
        
        # 筛选预算
        if budget:
            city_hotels = city_hotels[city_hotels['平均价格'] <= budget]
        
        # 随机选择top_n个酒店（可以根据实际情况实现更复杂的推荐算法）
        if len(city_hotels) > top_n:
            recommended = city_hotels.sample(n=top_n)
        else:
            recommended = city_hotels
        
        return recommended.to_dict('records')
    
    def recommend_dining(self, city, dining_type=None, budget=None, top_n=3):
        """推荐餐饮"""
        if self.dining_data.empty:
            return []
        
        # 筛选城市
        city_dining = self.dining_data[self.dining_data['城市'] == city]
        
        if city_dining.empty:
            return []
        
        # 筛选餐饮类型
        if dining_type:
            city_dining = city_dining[city_dining['类型'] == dining_type]
        
        # 筛选预算
        if budget:
            city_dining = city_dining[city_dining['人均价格'] <= budget]
        
        # 随机选择top_n个餐饮（可以根据实际情况实现更复杂的推荐算法）
        if len(city_dining) > top_n:
            recommended = city_dining.sample(n=top_n)
        else:
            recommended = city_dining
        
        return recommended.to_dict('records')
    
    def calculate_accommodation_cost(self, city, days, hotel_type='经济型酒店'):
        """计算住宿费用"""
        if self.hotels_data.empty:
            return 0
        
        city_hotels = self.hotels_data[self.hotels_data['城市'] == city]
        
        if city_hotels.empty:
            return 0
        
        # 筛选酒店类型
        type_hotels = city_hotels[city_hotels['类型'] == hotel_type]
        
        if type_hotels.empty:
            return 0
        
        # 计算平均价格
        avg_price = type_hotels['平均价格'].mean()
        
        return avg_price * days
    
    def calculate_dining_cost(self, city, days, meals_per_day=3, dining_type='中餐'):
        """计算餐饮费用"""
        if self.dining_data.empty:
            return 0
        
        city_dining = self.dining_data[self.dining_data['城市'] == city]
        
        if city_dining.empty:
            return 0
        
        # 筛选餐饮类型
        type_dining = city_dining[city_dining['类型'] == dining_type]
        
        if type_dining.empty:
            return 0
        
        # 计算平均价格
        avg_price = type_dining['人均价格'].mean()
        
        return avg_price * meals_per_day * days
