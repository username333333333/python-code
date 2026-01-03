from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils.data_loader import load_all_city_data, get_filter_options
import pandas as pd
from flask_login import login_required

query_view = Blueprint("query_view", __name__, url_prefix="/query")

@query_view.route("/", methods=["GET"])
@login_required
def index():
    df = load_all_city_data()

    filters = {
        "city": request.args.get("city", ""),
        "start_date": request.args.get("start_date", ""),
        "end_date": request.args.get("end_date", ""),
        "time_period": request.args.get("time_period", ""),
        "weather": request.args.get("weather", ""),
        "wind_dir": request.args.get("wind_dir", ""),
        "wind_lvl": request.args.get("wind_lvl", ""),
        "temp_min": request.args.get("temp_min", ""),
        "temp_max": request.args.get("temp_max", ""),
    }
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

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
    
    # ✅ 分页
    page_size = 20
    total_items = len(filtered)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    
    # 将日期转换为字符串格式，避免模板中处理类型问题
    page_data = filtered.iloc[start:end].copy()
    
    # 清理字段名，去除空格
    page_data.columns = page_data.columns.str.strip()
    
    if '日期' in page_data.columns:
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(page_data['日期']):
            page_data['日期'] = pd.to_datetime(page_data['日期'], errors='coerce')
        # 将日期转换为字符串格式
        page_data['日期'] = page_data['日期'].dt.strftime('%Y-%m-%d')
    
    page_data = page_data.to_dict(orient="records")

    return render_template(
        "query_view.html",
        data=page_data,
        filters={**filters, "page": page},
        options=get_filter_options(),
        pagination={
            "page": page,
            "total_pages": total_pages,
            "total_items": total_items
        },
        max=max,  # ✅ 解决 Jinja2 模板中 max 未定义问题
        min=min   # ✅ 同理
    )
