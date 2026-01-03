from datetime import datetime, time
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """普通用户表"""
    __tablename__ = 'user'  # 明确表名
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(64), nullable=True, default='')  # 昵称
    avatar = db.Column(db.String(255), nullable=True, default='')  # 头像URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # 用户是否激活
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查密码哈希"""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login要求的属性和方法
    @property
    def is_authenticated(self):
        """用户是否已认证"""
        return True
    
    @property
    def is_anonymous(self):
        """用户是否是匿名用户"""
        return False
    
    def get_id(self):
        """获取用户ID"""
        return f"user_{self.id}"
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        """检查用户是否为管理员"""
        return False


class LoginHistory(db.Model):
    """登录历史记录"""
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4/IPv6地址
    user_agent = db.Column(db.String(255), nullable=True)  # 用户浏览器信息
    login_result = db.Column(db.Boolean, default=True)  # 登录结果：True成功，False失败
    fail_reason = db.Column(db.String(100), nullable=True)  # 登录失败原因
    
    # 关系
    user = db.relationship('User', backref=db.backref('login_history', lazy=True))
    
    def __repr__(self):
        return f'<LoginHistory {self.user_id} @ {self.login_time} - {self.login_result}>'


class Favorite(db.Model):
    """用户收藏夹"""
    __tablename__ = 'favorite'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 普通用户ID，可为空
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)  # 管理员ID，可为空
    favorite_type = db.Column(db.String(20), nullable=False)  # 收藏类型：query, recommendation, prediction
    name = db.Column(db.String(100), nullable=False)  # 收藏名称
    content = db.Column(db.JSON, nullable=False)  # 收藏内容，JSON格式存储查询条件或推荐结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('favorites', lazy=True))
    
    def __repr__(self):
        return f'<Favorite {self.name}>'


class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'admin'  # 明确表名
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(64), nullable=True, default='')  # 昵称
    avatar = db.Column(db.String(255), nullable=True, default='')  # 头像URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # 管理员是否激活
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查密码哈希"""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login要求的属性和方法
    @property
    def is_authenticated(self):
        """用户是否已认证"""
        return True
    
    @property
    def is_anonymous(self):
        """用户是否是匿名用户"""
        return False
    
    def get_id(self):
        """获取管理员ID，格式为admin_1"""
        return f"admin_{self.id}"
    
    def __repr__(self):
        return f'<Admin {self.username}>'
    
    def is_admin(self):
        """检查用户是否为管理员"""
        return True


class Attraction(db.Model):
    """景点模型"""
    __tablename__ = 'attraction'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=True)
    duration = db.Column(db.String(50), nullable=True)  # 推荐游玩时长
    longitude = db.Column(db.Float, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    best_season = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attraction {self.name}>'


class TrafficRecord(db.Model):
    """客流量记录模型"""
    __tablename__ = 'traffic_record'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attraction.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    traffic = db.Column(db.Integer, nullable=False)
    weather = db.Column(db.String(50), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    is_holiday = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    attraction = db.relationship('Attraction', backref=db.backref('traffic_records', lazy=True))
    
    def __repr__(self):
        return f'<TrafficRecord {self.attraction_id} @ {self.date}: {self.traffic}>'


class RiskAssessment(db.Model):
    """风险评估记录模型"""
    __tablename__ = 'risk_assessment'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attraction.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    risk_level = db.Column(db.String(10), nullable=False)  # 低/中/高
    advice = db.Column(db.Text, nullable=True)
    weather_forecast = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    attraction = db.relationship('Attraction', backref=db.backref('risk_assessments', lazy=True))
    
    def __repr__(self):
        return f'<RiskAssessment {self.attraction_id} @ {self.date}: {self.risk_level}>'


class Itinerary(db.Model):
    """行程模型"""
    __tablename__ = 'itinerary'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    days = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    start_city = db.Column(db.String(50), nullable=False)  # 起点城市
    is_closed_loop = db.Column(db.Boolean, default=True)  # 是否为闭环路径
    preferences = db.Column(db.JSON, nullable=True)  # 存储用户偏好
    status = db.Column(db.String(20), default='draft')  # draft, active, completed
    
    # 关系
    user = db.relationship('User', backref=db.backref('itineraries', lazy=True))
    itinerary_days = db.relationship('ItineraryDay', backref='itinerary', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Itinerary {self.id} for User {self.user_id}>'


class ItineraryDay(db.Model):
    """行程天数模型"""
    __tablename__ = 'itinerary_day'
    
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    weather = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    itinerary_attractions = db.relationship('ItineraryAttraction', backref='itinerary_day', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ItineraryDay {self.itinerary_id}: Day {self.day_number}>'


class ItineraryAttraction(db.Model):
    """行程景点模型"""
    __tablename__ = 'itinerary_attraction'
    
    id = db.Column(db.Integer, primary_key=True)
    itinerary_day_id = db.Column(db.Integer, db.ForeignKey('itinerary_day.id'), nullable=False)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attraction.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    suggested_time = db.Column(db.Time, nullable=True)
    transportation = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    attraction = db.relationship('Attraction')
    
    def __repr__(self):
        return f'<ItineraryAttraction {self.id}: {self.attraction_id} at {self.suggested_time}>'
