from app.utils.data_loader import load_all_city_data
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np

class RiskAssessmentService:
    """出行风险决策服务
    
    结合天气数据和景点类型，构建旅游风险评估模型，对景点出行风险分级，并给出规避建议
    """
    
    def __init__(self, data_dir):
        """初始化服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        
        # 风险等级定义和描述
        self.risk_definitions = {
            '低': {
                'description': '风险较低，适合出行',
                'color': '#28a745',  # 绿色
                'advice_prefix': '可正常出行，建议：'
            },
            '中': {
                'description': '风险中等，需注意安全',
                'color': '#ffc107',  # 黄色
                'advice_prefix': '出行需谨慎，建议：'
            },
            '高': {
                'description': '风险较高，不建议出行',
                'color': '#dc3545',  # 红色
                'advice_prefix': '不建议出行，若必须前往，建议：'
            }
        }
        
        # 风险等级优先级（用于多条件评估）
        self.risk_levels = ['低', '中', '高']
        
        # 完善的风险评估规则
        self.risk_criteria = {
            # 景点类型: 风险评估规则
            '山地': {
                '暴雨': {'risk': '高', 'advice': '暴雨天易发生泥石流、滑坡等灾害，禁止登山'}, 
                '大暴雨': {'risk': '高', 'advice': '大暴雨天气山体稳定性极差，绝对禁止户外活动'}, 
                '特大暴雨': {'risk': '高', 'advice': '特大暴雨天气极端危险，必须立即撤离山区'}, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天注意高空坠物，远离悬崖边缘'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天禁止登山，易发生坠崖事故'}
                }, 
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '30-35℃高温天注意防暑，携带足够的水和防暑药品'}, 
                    '35℃以上': {'risk': '高', 'advice': '35℃以上高温天禁止长时间登山，易中暑'}
                }, 
                '低温': {
                    '-10-0℃': {'risk': '中', 'advice': '-10-0℃低温天注意保暖，穿防滑鞋和羽绒服'}, 
                    '-20--10℃': {'risk': '高', 'advice': '-20--10℃低温天易发生冻伤，不推荐登山'}, 
                    '-20℃以下': {'risk': '高', 'advice': '-20℃以下极端低温，绝对禁止登山'}
                }, 
                '大雾': {
                    '能见度100-500m': {'risk': '中', 'advice': '大雾天能见度低，注意路径标识，结伴而行'}, 
                    '能见度100m以下': {'risk': '高', 'advice': '能见度100m以下，极易迷路，禁止登山'}
                }, 
                '雷电': {'risk': '高', 'advice': '雷电天气禁止户外活动，远离山顶、树木和金属物体，找安全的室内躲避'},
                '冰雹': {'risk': '高', 'advice': '冰雹天气立即寻找躲避处，保护头部和重要部位'}
            },
            '海滨': {
                '台风': {
                    '热带低压(6-7级)': {'risk': '中', 'advice': '热带低压天气，避免下海，注意海浪变化'}, 
                    '热带风暴(8-9级)': {'risk': '高', 'advice': '热带风暴天气，远离海边，关闭门窗'}, 
                    '强热带风暴(10-11级)': {'risk': '高', 'advice': '强热带风暴天气，立即撤离危险区域'}, 
                    '台风(12级及以上)': {'risk': '高', 'advice': '台风天气，绝对禁止靠近海边，立即转移到安全地带'}
                }, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天不推荐下海游泳，注意海浪'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天禁止下海，巨浪风险极高'}
                }, 
                '暴雨': {
                    '25-50mm': {'risk': '中', 'advice': '暴雨天海边可能涨潮，注意安全，远离危险区域'}, 
                    '50mm以上': {'risk': '高', 'advice': '暴雨天易引发风暴潮，绝对禁止靠近海边'}
                }, 
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '30-35℃高温天注意防晒，涂抹防晒霜，多喝水'}, 
                    '35℃以上': {'risk': '高', 'advice': '35℃以上高温天避免长时间暴露在阳光下，防止中暑'}
                }, 
                '大浪': {
                    '2-3m': {'risk': '中', 'advice': '2-3m大浪天不推荐下海游泳，注意警示标志'}, 
                    '3m以上': {'risk': '高', 'advice': '3m以上大浪天禁止下海，极易发生溺水事故'}
                },
                '雷电': {'risk': '高', 'advice': '海边雷电天气禁止户外活动，立即寻找室内躲避'}
            },
            '户外': {
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '30-35℃高温天注意防暑，避免正午时分户外活动，携带足够的水'}, 
                    '35℃以上': {'risk': '高', 'advice': '35℃以上高温天避免户外活动，易中暑'}
                }, 
                '暴雨': {
                    '25-50mm': {'risk': '中', 'advice': '暴雨天减少户外活动，注意防滑和防雷'}, 
                    '50mm以上': {'risk': '高', 'advice': '暴雨天避免户外活动，防止触电和洪水'}
                }, 
                '雷电': {'risk': '高', 'advice': '雷电天气立即寻找安全的室内躲避，远离大树、电线杆等'}, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天注意高空坠物，远离广告牌和大树'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天避免户外活动，防止被物体砸伤'}
                }, 
                '低温': {
                    '-10-0℃': {'risk': '中', 'advice': '-10-0℃低温天注意保暖，穿合适的户外服装'}, 
                    '-20--10℃': {'risk': '高', 'advice': '-20--10℃低温天减少户外活动，防止冻伤'}, 
                    '-20℃以下': {'risk': '高', 'advice': '-20℃以下极端低温，禁止长时间户外活动'}
                },
                '大雾': {
                    '能见度100-500m': {'risk': '中', 'advice': '大雾天注意交通安全，减速慢行'}, 
                    '能见度100m以下': {'risk': '高', 'advice': '大雾天减少外出，必须外出时注意安全'}
                }
            },
            '室内': {
                '所有天气': {'risk': '低', 'advice': '室内活动不受天气影响，可正常出行'}
            },
            '主题乐园': {
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '30-35℃高温天注意防暑，合理安排游玩时间，避开正午时分'}, 
                    '35℃以上': {'risk': '高', 'advice': '35℃以上高温天易中暑，建议改期或选择室内项目'}
                }, 
                '暴雨': {
                    '25-50mm': {'risk': '低', 'advice': '暴雨天部分室外项目可能关闭，建议提前查看园区通知'}, 
                    '50mm以上': {'risk': '中', 'advice': '暴雨天大部分室外项目关闭，建议选择室内项目或改期'}
                }, 
                '大风': {
                    '6-7级': {'risk': '低', 'advice': '6-7级大风天部分高空项目可能关闭，注意园区通知'}, 
                    '8级及以上': {'risk': '中', 'advice': '8级及以上大风天大部分高空项目关闭，建议改期'}
                }, 
                '低温': {
                    '-10-0℃': {'risk': '低', 'advice': '低温天注意保暖，部分水上项目可能关闭'}, 
                    '-20--10℃': {'risk': '中', 'advice': '低温天大部分水上项目关闭，建议选择室内项目'}
                },
                '雷电': {'risk': '中', 'advice': '雷电天气室外项目关闭，建议选择室内项目或改期'}
            },
            '博物馆': {
                '所有天气': {'risk': '低', 'advice': '室内活动不受天气影响，可正常出行'}
            },
            '温泉': {
                '高温': {
                    '30-35℃': {'risk': '低', 'advice': '高温天泡温泉注意补充水分，每次浸泡不超过15分钟'}, 
                    '35℃以上': {'risk': '中', 'advice': '35℃以上高温天减少泡温泉时间，防止中暑'}
                }, 
                '低温': {
                    '-10-0℃': {'risk': '低', 'advice': '低温天泡温泉注意保暖，进出池时避免温差过大'}, 
                    '-20--10℃': {'risk': '中', 'advice': '低温天注意保暖，避免长时间暴露在寒冷环境中'}
                }, 
                '暴雨': {
                    '25-50mm': {'risk': '低', 'advice': '暴雨天不影响室内温泉，但注意室外行走安全'}, 
                    '50mm以上': {'risk': '中', 'advice': '暴雨天注意道路积水，谨慎驾车'}
                },
                '大风': {
                    '6-7级': {'risk': '低', 'advice': '大风天注意关好门窗，避免物品掉落'}, 
                    '8级及以上': {'risk': '中', 'advice': '大风天减少外出，注意高空坠物'}
                }
            },
            '滑雪': {
                '高温': {
                    '0℃以上': {'risk': '高', 'advice': '0℃以上高温天雪质融化，不适合滑雪'}, 
                    '0-5℃': {'risk': '中', 'advice': '0-5℃雪质变软，滑雪难度增加，注意安全'}
                }, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天注意安全，部分雪道可能关闭'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天能见度极低，禁止滑雪'}
                }, 
                '暴雨': {
                    '所有级别': {'risk': '高', 'advice': '暴雨天雪道湿滑，容易摔倒受伤，禁止滑雪'}
                }, 
                '暴雪': {
                    '所有级别': {'risk': '高', 'advice': '暴雪天气能见度极低，禁止滑雪，注意雪崩风险'}
                },
                '低温': {
                    '-20--10℃': {'risk': '中', 'advice': '-20--10℃低温天注意保暖，穿戴专业滑雪装备'}, 
                    '-30--20℃': {'risk': '高', 'advice': '-30--20℃低温天易发生冻伤，减少滑雪时间'}, 
                    '-30℃以下': {'risk': '高', 'advice': '-30℃以下极端低温，禁止滑雪'}
                }
            },
            '湖泊': {
                '暴雨': {
                    '25-50mm': {'risk': '中', 'advice': '暴雨天湖泊水位上涨，禁止下水游泳'}, 
                    '50mm以上': {'risk': '高', 'advice': '暴雨天易引发洪水，远离湖泊岸边'}
                }, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天湖面波浪较大，禁止划船和游泳'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天湖面可能掀起巨浪，绝对禁止靠近岸边'}
                }, 
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '高温天注意防晒，避免长时间暴露在阳光下'}, 
                    '35℃以上': {'risk': '中', 'advice': '高温天游泳注意安全，防止中暑和溺水'}
                },
                '雷电': {
                    '所有级别': {'risk': '高', 'advice': '湖泊区域是雷电高发区，雷电天气绝对禁止户外活动'}
                }
            },
            '森林': {
                '高温': {
                    '30-35℃': {'risk': '中', 'advice': '高温天注意防火，禁止吸烟和野外用火'}, 
                    '35℃以上': {'risk': '高', 'advice': '35℃以上高温天森林火险等级高，禁止进入林区'}
                }, 
                '干旱': {
                    '轻度干旱': {'risk': '中', 'advice': '轻度干旱天注意防火，遵守林区规定'}, 
                    '中度及以上干旱': {'risk': '高', 'advice': '中度及以上干旱天森林火险极高，禁止进入林区'}
                }, 
                '大风': {
                    '6-7级': {'risk': '中', 'advice': '6-7级大风天注意防火，禁止野外用火'}, 
                    '8级及以上': {'risk': '高', 'advice': '8级及以上大风天森林火险极高，禁止进入林区'}
                },
                '雷电': {
                    '所有级别': {'risk': '高', 'advice': '森林是雷电高发区，雷电天气立即撤离林区'}
                },
                '暴雨': {
                    '25-50mm': {'risk': '中', 'advice': '暴雨天注意防滑，避免进入峡谷区域'}, 
                    '50mm以上': {'risk': '高', 'advice': '暴雨天易引发山洪，立即撤离林区'}
                }
            }
        }
        
        # 初始化机器学习模型
        self.risk_model = None
        self.label_encoder = LabelEncoder()
        self.attraction_type_encoder = LabelEncoder()
        
        # 尝试训练机器学习模型
        self._train_risk_model()
        
    def _train_risk_model(self):
        """训练风险评估机器学习模型"""
        try:
            # 加载风险数据（假设存在风险数据集）
            risk_data_path = f"{self.data_dir}/risk/risk_assessment_data.csv"
            
            # 检查文件是否存在
            import os
            if not os.path.exists(risk_data_path):
                # 如果文件不存在，使用模拟数据训练模型
                self._train_with_synthetic_data()
                return
            
            # 读取风险数据
            risk_data = pd.read_csv(risk_data_path)
            
            # 准备特征和标签
            X = risk_data[['attraction_type', 'temperature', 'wind_speed', 'has_rain', 'has_snow', 'has_fog', 'has_thunder']]
            y = risk_data['risk_level']
            
            # 编码分类特征
            self.attraction_type_encoder.fit(X['attraction_type'])
            X['attraction_type'] = self.attraction_type_encoder.transform(X['attraction_type'])
            
            # 编码标签
            self.label_encoder.fit(y)
            y_encoded = self.label_encoder.transform(y)
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
            
            # 训练随机森林模型
            self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.risk_model.fit(X_train, y_train)
            
            # 评估模型
            y_pred = self.risk_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"风险评估模型训练完成，准确率: {accuracy:.2f}")
            
        except Exception as e:
            print(f"训练风险评估模型失败: {str(e)}")
            # 如果训练失败，使用模拟数据训练模型
            self._train_with_synthetic_data()
    
    def _train_with_synthetic_data(self):
        """使用模拟数据训练风险评估模型"""
        print("使用模拟数据训练风险评估模型")
        
        # 创建模拟数据
        # 使用当前时间作为随机种子，确保每次运行结果不同
        np.random.seed(int(datetime.now().timestamp()))
        
        # 生成1000条模拟数据
        n_samples = 1000
        
        # 生成特征
        attraction_types = ['山地', '海滨', '户外', '室内', '主题乐园', '博物馆', '温泉', '滑雪']
        X_attraction_type = np.random.choice(attraction_types, size=n_samples)
        X_temperature = np.random.randint(-20, 45, size=n_samples)
        X_wind_speed = np.random.randint(0, 20, size=n_samples)
        X_has_rain = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])
        X_has_snow = np.random.choice([0, 1], size=n_samples, p=[0.9, 0.1])
        X_has_fog = np.random.choice([0, 1], size=n_samples, p=[0.95, 0.05])
        X_has_thunder = np.random.choice([0, 1], size=n_samples, p=[0.98, 0.02])
        
        # 生成标签（基于简单规则）
        y = []
        for i in range(n_samples):
            risk = '低'
            if X_attraction_type[i] == '山地':
                if X_has_rain[i] and X_temperature[i] > 25:
                    risk = '高'
                elif X_wind_speed[i] > 10:
                    risk = '中'
            elif X_attraction_type[i] == '海滨':
                if X_wind_speed[i] > 15:
                    risk = '高'
                elif X_has_rain[i]:
                    risk = '中'
            elif X_attraction_type[i] == '户外':
                if X_has_rain[i] or X_has_thunder[i]:
                    risk = '高'
                elif X_temperature[i] > 35 or X_temperature[i] < -10:
                    risk = '中'
            y.append(risk)
        
        # 创建DataFrame
        X = pd.DataFrame({
            'attraction_type': X_attraction_type,
            'temperature': X_temperature,
            'wind_speed': X_wind_speed,
            'has_rain': X_has_rain,
            'has_snow': X_has_snow,
            'has_fog': X_has_fog,
            'has_thunder': X_has_thunder
        })
        
        # 编码特征
        self.attraction_type_encoder.fit(X['attraction_type'])
        X['attraction_type'] = self.attraction_type_encoder.transform(X['attraction_type'])
        
        # 编码标签
        self.label_encoder.fit(y)
        y_encoded = self.label_encoder.transform(y)
        
        # 训练模型
        self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.risk_model.fit(X, y_encoded)
        
        print("使用模拟数据训练完成")
    
    def _predict_risk_ml(self, attraction_type, weather_forecast):
        """使用机器学习模型预测风险等级"""
        if not self.risk_model:
            return None
        
        try:
            # 准备预测数据
            # 提取天气特征
            has_rain = 1 if '雨' in weather_forecast['weather'] else 0
            has_snow = 1 if '雪' in weather_forecast['weather'] else 0
            has_fog = 1 if '雾' in weather_forecast['weather'] else 0
            has_thunder = 1 if '雷' in weather_forecast['weather'] else 0
            
            # 创建特征向量
            feature_vector = pd.DataFrame({
                'attraction_type': [attraction_type],
                'temperature': [weather_forecast['temperature']],
                'wind_speed': [weather_forecast['wind']],
                'has_rain': [has_rain],
                'has_snow': [has_snow],
                'has_fog': [has_fog],
                'has_thunder': [has_thunder]
            })
            
            # 编码特征
            if attraction_type in self.attraction_type_encoder.classes_:
                feature_vector['attraction_type'] = self.attraction_type_encoder.transform(feature_vector['attraction_type'])
            else:
                # 如果景点类型不在训练数据中，使用默认值
                feature_vector['attraction_type'] = 0
            
            # 预测
            prediction_encoded = self.risk_model.predict(feature_vector)
            prediction = self.label_encoder.inverse_transform(prediction_encoded)[0]
            
            return prediction
        except Exception as e:
            print(f"使用机器学习模型预测风险失败: {str(e)}")
            return None
        
    def assess_risk(self, attraction_type, weather_forecast):
        """评估景点出行风险
        
        Args:
            attraction_type: 景点类型
            weather_forecast: 天气预报数据
            
        Returns:
            dict: 风险评估结果
        """
        # 获取景点类型对应的风险规则
        type_rules = self.risk_criteria.get(attraction_type, self.risk_criteria['户外'])
        
        # 初始化风险评估结果
        risk_result = {
            'risk_level': '低',
            'risk_description': self.risk_definitions['低']['description'],
            'advice': [],
            'weather_factors': [],
            'risk_source': 'rule_based',  # 默认使用规则引擎结果
            'risk_color': self.risk_definitions['低']['color']
        }
        
        # 提取天气因素
        weather = weather_forecast['weather']
        
        # 修复温度类型转换问题
        temp = weather_forecast['temperature']
        # 将温度转换为数字类型
        if isinstance(temp, str):
            # 尝试提取数字部分
            import re
            temp_match = re.search(r'[-+]?\d+\.?\d*', temp)
            temp = float(temp_match.group()) if temp_match else 20.0
        
        # 将风速转换为数字类型
        wind = weather_forecast['wind']
        if isinstance(wind, str):
            import re
            wind_match = re.search(r'[-+]?\d+\.?\d*', wind)
            wind = float(wind_match.group()) if wind_match else 0.0
        
        precipitation = weather_forecast.get('precipitation', 0)
        # 确保降水量是数字类型
        if isinstance(precipitation, str):
            import re
            precip_match = re.search(r'[-+]?\d+\.?\d*', precipitation)
            precipitation = float(precip_match.group()) if precip_match else 0.0
        
        # 评估风险
        assessed_risks = []
        
        # 检查温度风险
        if temp > 35:
            assessed_risks.append({'type': '高温', 'level': '35℃以上'})
        elif 30 <= temp <= 35:
            assessed_risks.append({'type': '高温', 'level': '30-35℃'})
        elif -10 <= temp < 0:
            assessed_risks.append({'type': '低温', 'level': '-10-0℃'})
        elif temp < -20:
            assessed_risks.append({'type': '低温', 'level': '-20℃以下'})
        elif -20 <= temp < -10:
            assessed_risks.append({'type': '低温', 'level': '-20--10℃'})
        
        # 检查降水风险
        # 优先使用降水量数据，确保准确评估
        if precipitation > 100:
            assessed_risks.append({'type': '暴雨', 'level': '特大暴雨'})
        elif precipitation > 50:
            assessed_risks.append({'type': '暴雨', 'level': '大暴雨'})
        elif precipitation > 25:
            assessed_risks.append({'type': '暴雨', 'level': '暴雨'})
        elif '雨' in weather:
            # 从天气描述中提取降水等级
            if '特大暴雨' in weather:
                assessed_risks.append({'type': '暴雨', 'level': '特大暴雨'})
            elif '大暴雨' in weather:
                assessed_risks.append({'type': '暴雨', 'level': '大暴雨'})
            elif '暴雨' in weather:
                assessed_risks.append({'type': '暴雨', 'level': '暴雨'})
            elif '大雨' in weather:
                # 当天气描述为大雨时，根据常识判断降水量在25-50mm之间，风险等级应为中或高
                assessed_risks.append({'type': '暴雨', 'level': '暴雨'})
            else:
                assessed_risks.append({'type': '暴雨', 'level': '小雨'})
        
        # 检查降雪风险
        if '雪' in weather:
            assessed_risks.append({'type': '降雪', 'level': '降雪'})
        
        # 检查雾风险
        if '雾' in weather:
            if '浓雾' in weather or '强浓雾' in weather or '特强浓雾' in weather:
                assessed_risks.append({'type': '大雾', 'level': '能见度100m以下'})
            else:
                assessed_risks.append({'type': '大雾', 'level': '能见度100-500m'})
        
        # 检查极端天气风险
        if '霾' in weather:
            assessed_risks.append({'type': '霾', 'level': '能见度500m以下'})
        elif '沙尘暴' in weather:
            assessed_risks.append({'type': '沙尘暴', 'level': '能见度1000m以下'})
        elif '龙卷风' in weather:
            assessed_risks.append({'type': '龙卷风', 'level': '极端天气'})
        elif '冰雹' in weather:
            assessed_risks.append({'type': '冰雹', 'level': '极端天气'})
        
        # 检查雷电风险
        if '雷' in weather:
            assessed_risks.append({'type': '雷电', 'level': '雷电'})
        
        # 检查风力风险
        if wind > 12:
            assessed_risks.append({'type': '大风', 'level': '8级及以上'})
        elif wind > 6:
            assessed_risks.append({'type': '大风', 'level': '6-7级'})
        
        # 根据评估的风险因素获取风险等级和建议
        for risk_factor in assessed_risks:
            factor_type = risk_factor['type']
            factor_level = risk_factor['level']
            
            # 获取对应风险规则
            if factor_type in type_rules:
                # 检查是否是多级风险规则
                factor_rules = type_rules[factor_type]
                if isinstance(factor_rules, dict):
                    # 多级风险规则，根据级别匹配
                    risk_info = factor_rules.get(factor_level, {'risk': '低', 'advice': ''})
                else:
                    # 单级风险规则
                    risk_info = factor_rules
                
                risk_result['weather_factors'].append(f"{factor_type}: {factor_level}")
                
                # 更新风险等级
                if self.risk_levels.index(risk_info['risk']) > self.risk_levels.index(risk_result['risk_level']):
                    risk_result['risk_level'] = risk_info['risk']
                    risk_result['risk_description'] = self.risk_definitions[risk_info['risk']]['description']
                    risk_result['risk_color'] = self.risk_definitions[risk_info['risk']]['color']
                
                # 添加建议
                risk_result['advice'].append(risk_info['advice'])
        
        # 如果没有评估到风险，添加默认建议
        if not risk_result['advice']:
            default_advice = type_rules.get('所有天气', {'advice': f'{attraction_type}适合当前天气，可正常出行', 'risk': '低'})
            risk_result['advice'].append(default_advice['advice'])
        
        # 使用机器学习模型预测风险
        ml_risk = self._predict_risk_ml(attraction_type, weather_forecast)
        if ml_risk:
            # 结合规则引擎和机器学习结果
            # 如果机器学习结果的风险等级更高，则使用机器学习结果
            if self.risk_levels.index(ml_risk) > self.risk_levels.index(risk_result['risk_level']):
                risk_result['risk_level'] = ml_risk
                risk_result['risk_description'] = self.risk_definitions[ml_risk]['description']
                risk_result['risk_color'] = self.risk_definitions[ml_risk]['color']
                risk_result['risk_source'] = 'ml'
            elif self.risk_levels.index(ml_risk) == self.risk_levels.index(risk_result['risk_level']):
                # 如果风险等级相同，保留规则引擎结果，但记录机器学习结果
                risk_result['risk_source'] = 'combined'
        
        # 整理建议，添加风险等级前缀
        if risk_result['advice']:
            advice_prefix = self.risk_definitions[risk_result['risk_level']]['advice_prefix']
            risk_result['advice'] = [advice_prefix + advice for advice in risk_result['advice']]
        
        return risk_result
    
    def assess_batch_risk(self, attraction_type, weather_forecasts):
        """批量评估多天的风险
        
        Args:
            attraction_type: 景点类型
            weather_forecasts: 多天天气预报数据
            
        Returns:
            list: 每天的风险评估结果
        """
        results = []
        
        for forecast in weather_forecasts:
            risk_result = self.assess_risk(attraction_type, forecast)
            results.append({
                'date': forecast['date'],
                'weather': forecast['weather'],
                'temperature': forecast['temperature'],
                'wind': forecast['wind'],
                **risk_result
            })
        
        return results
    
    def get_safe_travel_dates(self, attraction_type, weather_forecasts):
        """获取安全出行日期
        
        Args:
            attraction_type: 景点类型
            weather_forecasts: 多天天气预报数据
            
        Returns:
            list: 安全出行日期列表
        """
        safe_dates = []
        
        for forecast in weather_forecasts:
            risk_result = self.assess_risk(attraction_type, forecast)
            
            # 只返回风险等级为低的日期
            if risk_result['risk_level'] == '低':
                safe_dates.append({
                    'date': forecast['date'],
                    'weather': forecast['weather'],
                    'temperature': forecast['temperature'],
                    'wind': forecast['wind'],
                    'advice': risk_result['advice']
                })
        
        return safe_dates
    
    def classify_attraction_type(self, attraction_name, attraction_desc):
        """根据景点名称和描述分类景点类型
        
        Args:
            attraction_name: 景点名称
            attraction_desc: 景点描述
            
        Returns:
            str: 景点类型
        """
        name = attraction_name.lower()
        desc = attraction_desc.lower() if attraction_desc else ''
        
        # 根据关键词分类
        if any(keyword in name or keyword in desc for keyword in ['山', '峰', '岭', '登山']):
            return '山地'
        elif any(keyword in name or keyword in desc for keyword in ['海', '滩', '岛', '滨海', '海滨']):
            return '海滨'
        elif any(keyword in name or keyword in desc for keyword in ['博物馆', '展览馆', '纪念馆', '美术馆', '科技馆', '图书馆']):
            return '室内'
        elif any(keyword in name or keyword in desc for keyword in ['乐园', '公园', '主题', '游乐场']):
            return '主题乐园'
        elif any(keyword in name or keyword in desc for keyword in ['温泉', '泡池', '汤泉']):
            return '温泉'
        elif any(keyword in name or keyword in desc for keyword in ['滑雪', '滑雪场', '雪场']):
            return '滑雪'
        elif any(keyword in name or keyword in desc for keyword in ['户外', '露营', '徒步', '骑行', '越野']):
            return '户外'
        else:
            # 默认分类为户外
            return '户外'
    
    def get_risk_criteria(self, attraction_type=None):
        """获取风险评估标准
        
        Args:
            attraction_type: 景点类型，None表示获取所有
            
        Returns:
            dict: 风险评估标准
        """
        if attraction_type:
            return {attraction_type: self.risk_criteria.get(attraction_type, {})}
        else:
            return self.risk_criteria
    
    def get_risk_level_color(self, risk_level):
        """获取风险等级对应的颜色
        
        Args:
            risk_level: 风险等级
            
        Returns:
            str: 颜色代码
        """
        return self.risk_definitions.get(risk_level, {}).get('color', '#6c757d')  # 默认灰色
    
    def generate_risk_report(self, attraction_name, attraction_desc, weather_forecasts):
        """生成风险评估报告
        
        Args:
            attraction_name: 景点名称
            attraction_desc: 景点描述
            weather_forecasts: 天气预报数据
            
        Returns:
            dict: 风险评估报告
        """
        # 分类景点类型
        attraction_type = self.classify_attraction_type(attraction_name, attraction_desc)
        
        # 批量评估风险
        risk_results = self.assess_batch_risk(attraction_type, weather_forecasts)
        
        # 获取安全出行日期
        safe_dates = self.get_safe_travel_dates(attraction_type, weather_forecasts)
        
        # 生成报告
        report = {
            'attraction_name': attraction_name,
            'attraction_type': attraction_type,
            'attraction_desc': attraction_desc,
            'risk_assessment': risk_results,
            'safe_travel_dates': safe_dates,
            'summary': {
                'total_days': len(weather_forecasts),
                'safe_days': len(safe_dates),
                'risk_distribution': {
                    '低': sum(1 for r in risk_results if r['risk_level'] == '低'),
                    '中': sum(1 for r in risk_results if r['risk_level'] == '中'),
                    '高': sum(1 for r in risk_results if r['risk_level'] == '高')
                }
            }
        }
        
        return report