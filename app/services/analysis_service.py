import pandas as pd
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from datetime import datetime
import os
from pyecharts.charts import Map, Line, Bar, Scatter, Pie, HeatMap, Timeline
from pyecharts import options as opts
from pyecharts.globals import ThemeType


class AnalysisService:
    city_coords = {
        "沈阳": [123.4328, 41.8086],
        "大连": [121.6186, 38.9146],
        "鞍山": [122.9946, 41.1106],
        "抚顺": [123.9298, 41.8773],
        "本溪": [123.7781, 41.3258],
        "丹东": [124.3385, 40.1290],
        "锦州": [121.1477, 41.1309],
        "营口": [122.2354, 40.6674],
        "阜新": [121.6608, 42.0193],
        "辽阳": [123.1728, 41.2733],
        "盘锦": [122.0707, 41.1199],
        "铁岭": [123.8548, 42.2998],
        "朝阳": [120.4461, 41.5718],
        "葫芦岛": [120.8365, 40.7110],
    }

    @staticmethod
    def create_liaoning_temp_map(df):
        if df.empty or '城市' not in df.columns:
            return Map().add("平均气温", [], "liaoning")

        grouped = df.groupby('城市').agg({'最高气温': 'mean', '最低气温': 'mean'}).reset_index()
        grouped['平均气温'] = grouped[['最高气温', '最低气温']].mean(axis=1)
        grouped['城市'] = grouped['城市'].apply(lambda x: x if x.endswith("市") else x + "市")

        data = list(zip(grouped['城市'], grouped['平均气温'].round(1)))

        # 使用连续的颜色渐变，从蓝色（低温）到红色（高温）
        return (
            Map(init_opts=opts.InitOpts(width="100%", height="500px"))
            .add("平均气温（°C）", data, "liaoning", 
                 label_opts=opts.LabelOpts(is_show=True, font_size=10))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True, font_size=10))
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="辽宁各市平均气温",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight="bold")
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=float(grouped['平均气温'].min()),
                    max_=float(grouped['平均气温'].max()),
                    is_calculable=True,
                    range_color=['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
                    orient="horizontal",
                    pos_bottom="10%",
                    pos_left="center",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                )
            )
        )


    @staticmethod
    def create_liaoning_wind_map(df):
        if df.empty or '城市' not in df.columns:
            return Map().add("平均风力", [], "liaoning")

        grouped = df.groupby('城市').agg({
            '风力(白天)_数值': 'mean',
            '风力(夜间)_数值': 'mean'
        }).reset_index()
        grouped['平均风力'] = grouped[['风力(白天)_数值', '风力(夜间)_数值']].mean(axis=1)
        grouped['城市'] = grouped['城市'].apply(lambda x: x if x.endswith("市") else x + "市")

        data = list(zip(grouped['城市'], grouped['平均风力'].round(1)))

        # 使用连续的颜色渐变，从浅蓝色（微风）到深蓝色（强风）
        return (
            Map(init_opts=opts.InitOpts(width="100%", height="500px"))
            .add("平均风力", data, "liaoning",
                 label_opts=opts.LabelOpts(is_show=True, font_size=10))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True, font_size=10))
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="辽宁各市平均风力",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight="bold")
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=float(grouped['平均风力'].min()),
                    max_=float(grouped['平均风力'].max()),
                    is_calculable=True,
                    range_color=['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
                    orient="horizontal",
                    pos_bottom="10%",
                    pos_left="center",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                )
            )
        )

    @staticmethod
    def create_temp_line_chart(data):
        if data.empty:
            chart = Line()
            chart.add_xaxis([])
            chart.add_yaxis("温度", [])
            return chart

        if len(data) > 1000:
            data = data.sample(1000, random_state=42).sort_values('日期')

        data = data.sort_values('日期')
        
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['日期']):
            data['日期'] = pd.to_datetime(data['日期'])
            
        x_data = data['日期'].dt.strftime('%Y-%m-%d').tolist()
        high_temp = data['最高气温'].ffill().bfill().fillna(0).tolist()
        low_temp = data['最低气温'].ffill().bfill().fillna(0).tolist()

        return (
            Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis(
                "最高气温", 
                high_temp,
                symbol="circle",
                symbol_size=6
            )
            .add_yaxis(
                "最低气温", 
                low_temp,
                symbol="circle",
                symbol_size=6
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="气温变化趋势",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight="bold")
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(255, 255, 255, 0.95)",
                    border_color="#ccc",
                    border_width=1,
                    formatter="{b}<br/>{a}: {c}°C"
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(type_="inside"),
                    opts.DataZoomOpts(type_="slider")
                ],
                yaxis_opts=opts.AxisOpts(
                    name="温度(℃)",
                    name_textstyle_opts=opts.TextStyleOpts(font_size=12, font_weight="bold"),
                    axislabel_opts=opts.LabelOpts(formatter="{value}°C")
                ),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=45, font_size=10)
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="30px",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                )
            )
        )

    @staticmethod
    def create_weather_bar_chart(data):
        if data.empty:
            chart = Bar()
            chart.add_xaxis([])
            chart.add_yaxis("天气", [])
            return chart

        weather_counts = data['天气状况(白天)'].value_counts().nlargest(10).reset_index()
        weather_counts.columns = ['天气', '天数']

        avg_temps = []
        for weather in weather_counts['天气']:
            subset = data[data['天气状况(白天)'] == weather]
            avg_high = subset['最高气温'].mean()
            avg_low = subset['最低气温'].mean()
            avg_temps.append(f"平均:{avg_high:.1f}°/{avg_low:.1f}°")

        bar = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(weather_counts['天气'].tolist())
            .add_yaxis("出现天数", weather_counts['天数'].tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="天气频率统计"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="出现天数"),
                xaxis_opts=opts.AxisOpts(name="天气类型", axislabel_opts=opts.LabelOpts(rotate=30))
            )
        )

        bar.options['series'][0]['data'] = [
            {"value": count, "avg_temp": temp}
            for count, temp in zip(weather_counts['天数'], avg_temps)
        ]

        return bar

    @staticmethod
    def create_wind_scatter_chart(data):
        if data.empty:
            chart = Scatter()
            chart.add_xaxis([])
            chart.add_yaxis("风力", [])
            return chart

        sample_data = data.sample(min(500, len(data)), random_state=42).sort_values('日期')
        x_data = sample_data['日期'].dt.strftime('%Y-%m-%d').tolist()

        wind_day = sample_data['风力(白天)_数值'].clip(0, 10).tolist()
        wind_night = sample_data['风力(夜间)_数值'].clip(0, 10).tolist()

        def get_symbol_size(wind):
            return 8 + wind * 2

        return (
            Scatter(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("白天风力", wind_day, symbol_size=[get_symbol_size(w) for w in wind_day])
            .add_yaxis("夜间风力", [-w for w in wind_night], symbol_size=[get_symbol_size(w) for w in wind_night])
            .set_global_opts(
                title_opts=opts.TitleOpts(title="风力分布"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                yaxis_opts=opts.AxisOpts(name="风力（正为白天，负为夜间）", min_=-10, max_=10),
                xaxis_opts=opts.AxisOpts(name="日期", axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )

    @staticmethod
    def create_season_pie_chart(data, is_day=True):
        if data.empty:
            return Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))

        col = "天气状况(白天)" if is_day else "天气状况(夜间)"
        prefix = "白天" if is_day else "夜间"

        # 直接创建一个饼图，而不是Timeline，因为预测数据通常只有7/14天，不需要按季度显示
        weather_counts = data[col].value_counts()
        total = weather_counts.sum()
        if total == 0:
            return Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))

        main_data = weather_counts[weather_counts / total >= 0.05]
        other_sum = total - main_data.sum()
        if other_sum > 0:
            main_data["其他"] = other_sum

        pie_data = [(weather, count) for weather, count in main_data.items()]

        # 确保有数据才添加到饼图
        if not pie_data:
            return Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))

        pie = (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add(
                f"{prefix}天气分布",
                pie_data,
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(
                    formatter="{b}: {d}%",
                    font_size=12
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{prefix}天气分布",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=16, font_weight="bold")
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                )
            )
        )

        return pie

    @staticmethod
    def create_temp_heatmap(data):
        if data.empty:
            return HeatMap(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['日期']):
            data['日期'] = pd.to_datetime(data['日期'])
        
        # 计算月份与日期
        data['month'] = data['日期'].dt.month
        data['day'] = data['日期'].dt.day
        
        # 对于未来预测数据，由于只有几天，使用更简单的热力图展示
        if len(data) <= 14:
            # 使用日期作为X轴，显示未来几天的气温
            data = data.sort_values('日期')
            x_axis = [date.strftime('%Y-%m-%d') for date in data['日期']]
            
            # 生成热力图数据
            heatmap_data = []
            for i, (_, row) in enumerate(data.iterrows()):
                heatmap_data.append([i, 0, round(row['最高气温'], 1)])
                heatmap_data.append([i, 1, round(row['最低气温'], 1)])
            
            # 构建图表
            heatmap = HeatMap(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            heatmap.add_xaxis(x_axis)
            heatmap.add_yaxis("气温类型", ["最高气温", "最低气温"], heatmap_data)
            heatmap.set_global_opts(
                title_opts=opts.TitleOpts(title="未来气温热力图"),
                visualmap_opts=opts.VisualMapOpts(min_=-10, max_=40, range_text=["低温", "高温"], is_calculable=True),
                tooltip_opts=opts.TooltipOpts()
            )
            return heatmap
        else:
            # 常规热力图，用于历史数据
            agg_data = data.groupby(['month', 'day'])['最高气温'].mean().reset_index()

            # 生成热力图数据
            heatmap_data = []
            for _, row in agg_data.iterrows():
                heatmap_data.append([row['month'] - 1, row['day'] - 1, round(row['最高气温'], 1)])

            # 获取时间范围字符串
            start_date = data['日期'].min().strftime('%Y-%m-%d')
            end_date = data['日期'].max().strftime('%Y-%m-%d')
            title_str = f"月度气温热力图（{start_date} ~ {end_date}）"

            # 构建图表
            heatmap = HeatMap(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            heatmap.add_xaxis([f"{m}月" for m in range(1, 13)])
            heatmap.add_yaxis("平均气温", [f"{d}日" for d in range(1, 32)], heatmap_data)
            heatmap.set_global_opts(
                title_opts=opts.TitleOpts(title=title_str),
                visualmap_opts=opts.VisualMapOpts(min_=-10, max_=40, range_text=["低温", "高温"], is_calculable=True),
                tooltip_opts=opts.TooltipOpts()
            )
            return heatmap

    @staticmethod
    def calculate_travel_score(data):
        """根据天气、气温、风力综合计算每日出游指数"""
        if data.empty:
            return pd.DataFrame(columns=['日期', '评分'])

        df = data.copy()

        # 温度评分：理想范围20~28分数最高
        df['temp_score'] = df[['最高气温', '最低气温']].mean(axis=1).apply(
            lambda t: 100 if 20 <= t <= 28 else max(0, 100 - abs(t - 24) * 5)
        )

        # 天气评分
        ideal_weather = ['晴', '多云']
        df['weather_score'] = df['天气状况(白天)'].apply(
            lambda w: 100 if any(iw in w for iw in ideal_weather) else 60 if '阴' in w else 30
        )

        # 风力评分（理想风力1-3级）
        df['wind_score'] = 100  # 默认值
        
        # 检查是否有风力数值列
        if '风力(白天)_数值' in df.columns:
            # 使用直接的数值列
            df['wind_score'] = df['风力(白天)_数值'].apply(
                lambda w: 100 if 1 <= w <= 3 else max(0, 100 - abs(w - 2) * 20)
            )
        elif '风力(白天)' in df.columns:
            # 使用字符串列
            def parse_wind(wind_str):
                try:
                    if '-' in wind_str:
                        parts = wind_str.replace('级', '').split('-')
                        return (int(parts[0]) + int(parts[1])) / 2
                    elif wind_str.endswith('级'):
                        return int(wind_str.replace('级', ''))
                except:
                    return 0
                return 0
            
            df['风力数值'] = df['风力(白天)'].apply(parse_wind)
            df['wind_score'] = df['风力数值'].apply(
                lambda w: 100 if 1 <= w <= 3 else max(0, 100 - abs(w - 2) * 20)
            )

        # 计算综合评分
        df['评分'] = df[['temp_score', 'weather_score', 'wind_score']].mean(axis=1)
        return df[['日期', '评分']].sort_values('评分', ascending=False).head(10)

    @staticmethod
    def create_top10_score_chart(score_df):
        """创建旅游出行指数 Top10 图表"""
        if score_df.empty:
            return Bar().add_xaxis([]).add_yaxis("出行评分", [])

        x_data = score_df['日期'].dt.strftime('%Y-%m-%d').tolist()
        y_data = score_df['评分'].round(2).tolist()

        return (
            Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("出行评分", y_data, category_gap="40%")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="出行推荐指数 Top10"),
                yaxis_opts=opts.AxisOpts(name="评分 (0-100)"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
                tooltip_opts=opts.TooltipOpts(trigger="axis")
            )
        )

    @staticmethod
    def create_travel_score_trend_chart(data):
        """创建旅游评分趋势图"""
        if data.empty:
            return Line(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        if len(data) > 1000:
            data = data.sample(1000, random_state=42).sort_values('日期')
            
        data = data.sort_values('日期')
        x_data = data['日期'].dt.strftime('%Y-%m-%d').tolist()
        y_data = data['旅游评分'].tolist()
        
        # 创建数据标签，只显示部分关键数据点
        label_points = []
        for i, value in enumerate(y_data):
            # 只在数据变化较大或重要点显示标签
            if i == 0 or i == len(y_data) - 1 or abs(value - y_data[i-1]) > 10:
                label_points.append(opts.LabelOpts(
                    formatter="{c}",
                    position="top",
                    font_size=10,
                    color="#333"
                ))
            else:
                label_points.append(opts.LabelOpts(is_show=False))
        
        return (
            Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis(
                "旅游评分", 
                y_data,
                is_smooth=True,
                symbol="circle",
                symbol_size=6
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="旅游评分趋势",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight="bold")
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(255, 255, 255, 0.95)",
                    border_color="#ccc",
                    border_width=1,
                    formatter="{b}<br/>{a}: {c}分"
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(type_="inside"),
                    opts.DataZoomOpts(type_="slider")
                ],
                yaxis_opts=opts.AxisOpts(
                    name="评分 (0-100)",
                    name_textstyle_opts=opts.TextStyleOpts(font_size=12, font_weight="bold"),
                    axislabel_opts=opts.LabelOpts(formatter="{value}分"),
                    min_=0,
                    max_=100
                ),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=45, font_size=10)
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="30px",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                )
            )
        )

    @staticmethod
    def create_season_travel_chart(data):
        """创建季节旅游推荐图"""
        if data.empty or '季节' not in data.columns or '旅游评分' not in data.columns:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        season_order = ['春季', '夏季', '秋季', '冬季']
        season_data = data.groupby('季节')['旅游评分'].mean().reset_index()
        season_data = season_data.set_index('季节').reindex(season_order).reset_index()
        
        x_data = season_data['季节'].tolist()
        y_data = season_data['旅游评分'].round(2).tolist()
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("平均旅游评分", y_data, category_gap="30%")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各季节平均旅游评分"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="评分 (0-100)", min_=0, max_=100)
            )
        )

    @staticmethod
    def create_travel_recommendation_pie(data):
        """创建旅游推荐指数分布饼图"""
        if data.empty or '推荐指数' not in data.columns:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        rec_counts = data['推荐指数'].value_counts().reset_index()
        rec_counts.columns = ['推荐指数', '天数']
        
        # 确保推荐指数顺序
        rec_order = ['强烈推荐', '推荐', '一般', '不推荐']
        rec_counts = rec_counts.set_index('推荐指数').reindex(rec_order).reset_index()
        rec_counts = rec_counts.dropna()
        
        return (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add(
                "",
                [list(z) for z in zip(rec_counts['推荐指数'], rec_counts['天数'])],
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(formatter="{b}: {d}%")
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="旅游推荐指数分布"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="middle", pos_left="left")
            )
        )

    @staticmethod
    def create_temp_travel_scatter(data):
        """创建温度与旅游评分关系散点图"""
        if data.empty:
            return Scatter(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        if len(data) > 1000:
            data = data.sample(1000, random_state=42)
            
        data['平均气温'] = (data['最高气温'] + data['最低气温']) / 2
        
        return (
            Scatter(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(data['平均气温'].tolist())
            .add_yaxis("旅游评分", data['旅游评分'].tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="温度与旅游评分关系"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                xaxis_opts=opts.AxisOpts(name="平均气温(℃)"),
                yaxis_opts=opts.AxisOpts(name="旅游评分(0-100)")
            )
        )

    @staticmethod
    def create_city_travel_comparison(data):
        """创建城市旅游评分对比图"""
        if data.empty or '城市' not in data.columns:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        city_scores = data.groupby('城市')['旅游评分'].mean().reset_index()
        city_scores = city_scores.sort_values('旅游评分', ascending=False)
        
        x_data = city_scores['城市'].tolist()
        y_data = city_scores['旅游评分'].round(2).tolist()
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("平均旅游评分", y_data, category_gap="30%")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="辽宁省各城市平均旅游评分"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="评分 (0-100)"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
            )
        )

    @staticmethod
    def create_weather_pie_chart(data, is_day=True):
        if data.empty:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))

        column = "天气状况(白天)" if is_day else "天气状况(夜间)"
        title = "白天天气状况" if is_day else "夜间天气状况"

        weather_counts = data[column].value_counts().reset_index()
        weather_counts.columns = ['天气', '天数']
        
        # 确保有数据才创建图表
        if weather_counts.empty:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))

        return (
            Pie(init_opts=opts.InitOpts(width="100%", height="400px"))
            .add(
                "",
                [list(z) for z in zip(weather_counts['天气'], weather_counts['天数'])],
                radius=["40%", "70%"],  # 环形图效果
                label_opts=opts.LabelOpts(
                    formatter="{b}: {d}%",  # 标签格式：天气：百分比
                    position="outside",  # 标签在外侧
                    color="#000",  # 标签颜色
                    font_size=12
                ),
                # 注意：旧版本中不能显式设置 label_line_opts，使用默认引导线即可
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="middle", pos_left="left"),
                toolbox_opts=opts.ToolboxOpts(is_show=True)
            )
        )

    @staticmethod
    def create_wind_direction_rose_chart(data, is_day=True):
        if data.empty:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))

        column = "风向(白天)" if is_day else "风向(夜间)"
        title = "白天风向分布" if is_day else "夜间风向分布"

        direction_counts = data[column].value_counts().reset_index()
        direction_counts.columns = ['风向', '次数']
        
        # 确保有数据才创建图表
        if direction_counts.empty:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))

        return (
            Pie(init_opts=opts.InitOpts(width="100%", height="400px"))
            .add(
                series_name="风向",
                data_pair=[(row['风向'], row['次数']) for _, row in direction_counts.iterrows()],
                radius=["20%", "70%"],  # 控制玫瑰花瓣大小范围
                rosetype="radius",  # 按半径区分大小
                label_opts=opts.LabelOpts(
                    position="outside",
                    formatter="{b}\n{c}次 ({d}%)",
                    font_size=12
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="middle", pos_left="left"),
                toolbox_opts=opts.ToolboxOpts(is_show=True)
            )
        )
    
    @staticmethod
    def create_traffic_trend_chart(data):
        """创建客流量趋势图"""
        if data.empty or '客流量' not in data.columns or '日期' not in data.columns:
            return Line(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        data = data.sort_values('日期')
        x_data = data['日期'].dt.strftime('%Y-%m-%d').tolist()
        y_data = data['客流量'].tolist()
        
        return (
            Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("客流量", y_data, is_smooth=True)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="客流量趋势图"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="客流量"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )
    
    @staticmethod
    def create_holiday_traffic_comparison(data):
        """创建节假日与非节假日客流量对比图"""
        if data.empty or '客流量' not in data.columns or '是否节假日' not in data.columns:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        holiday_data = data[data['是否节假日'] == 1]['客流量'].mean()
        non_holiday_data = data[data['是否节假日'] == 0]['客流量'].mean()
        
        x_data = ['节假日', '非节假日']
        y_data = [holiday_data, non_holiday_data]
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("平均客流量", y_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="节假日与非节假日客流量对比"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="平均客流量")
            )
        )
    
    @staticmethod
    def create_weather_traffic_scatter(data):
        """创建天气与客流量关系散点图"""
        if data.empty or '客流量' not in data.columns or '天气' not in data.columns:
            return Scatter(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        weather_mapping = {
            '晴': 1,
            '多云': 2,
            '阴': 3,
            '小雨': 4,
            '中雨': 5,
            '大雨': 6,
            '雪': 7
        }
        
        data['weather_code'] = data['天气'].map(weather_mapping).fillna(0)
        
        return (
            Scatter(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(data['weather_code'].tolist())
            .add_yaxis("客流量", data['客流量'].tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="天气与客流量关系"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                xaxis_opts=opts.AxisOpts(name="天气类型", min_=0, max_=8,
                                        axislabel_opts=opts.LabelOpts(formatter=lambda x: 
                                            list(weather_mapping.keys())[list(weather_mapping.values()).index(int(x))] if int(x) in weather_mapping.values() else "其他")),
                yaxis_opts=opts.AxisOpts(name="客流量")
            )
        )
    
    @staticmethod
    def create_attraction_traffic_ranking(data):
        """创建各景点客流量排名图"""
        if data.empty or '景点名称' not in data.columns or '客流量' not in data.columns:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        attraction_traffic = data.groupby('景点名称')['客流量'].mean().reset_index()
        attraction_traffic = attraction_traffic.sort_values('客流量', ascending=False).head(10)
        
        x_data = attraction_traffic['景点名称'].tolist()
        y_data = attraction_traffic['客流量'].round(0).tolist()
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("平均客流量", y_data)
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各景点客流量排名Top10"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="平均客流量"),
                yaxis_opts=opts.AxisOpts(name="景点名称", axislabel_opts=opts.LabelOpts(font_size=10))
            )
        )
    
    @staticmethod
    def create_seasonal_traffic_chart(data):
        """创建季节性客流量变化图"""
        if data.empty or '客流量' not in data.columns or '日期' not in data.columns:
            return Line(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        data['season'] = data['日期'].dt.month.apply(lambda x: 
            '春季' if 3 <= x <= 5 else '夏季' if 6 <= x <= 8 else '秋季' if 9 <= x <= 11 else '冬季')
        
        seasonal_traffic = data.groupby('season')['客流量'].mean().reset_index()
        season_order = ['春季', '夏季', '秋季', '冬季']
        seasonal_traffic = seasonal_traffic.set_index('season').reindex(season_order).reset_index()
        
        x_data = seasonal_traffic['season'].tolist()
        y_data = seasonal_traffic['客流量'].round(0).tolist()
        
        return (
            Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("平均客流量", y_data, is_smooth=True)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="季节性客流量变化"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="平均客流量")
            )
        )
    
    @staticmethod
    def create_risk_level_distribution(data):
        """创建风险等级分布饼图"""
        if data.empty or '风险等级' not in data.columns:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        risk_counts = data['风险等级'].value_counts().reset_index()
        risk_counts.columns = ['风险等级', '天数']
        
        return (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add("", [list(z) for z in zip(risk_counts['风险等级'], risk_counts['天数'])],
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="风险等级分布"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="middle", pos_left="left")
            )
        )
    
    @staticmethod
    def create_risk_level_time_trend(data):
        """创建风险等级时间变化图"""
        if data.empty or '风险等级' not in data.columns or '日期' not in data.columns:
            return Line(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        data = data.sort_values('日期')
        risk_mapping = {'低': 1, '中': 2, '高': 3}
        data['risk_code'] = data['风险等级'].map(risk_mapping).fillna(0)
        
        x_data = data['日期'].dt.strftime('%Y-%m-%d').tolist()
        y_data = data['risk_code'].tolist()
        
        return (
            Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("风险等级", y_data, is_smooth=True)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="风险等级时间变化"),
                tooltip_opts=opts.TooltipOpts(trigger="axis", formatter="{b}<br/>{a}: {c}"),
                yaxis_opts=opts.AxisOpts(name="风险等级", min_=0, max_=4,
                                        axislabel_opts=opts.LabelOpts(formatter=lambda x: 
                                            list(risk_mapping.keys())[list(risk_mapping.values()).index(int(x))] if int(x) in risk_mapping.values() else "无")),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )
    
    @staticmethod
    def create_weather_risk_relationship(data):
        """创建天气与风险等级关系图"""
        if data.empty or '风险等级' not in data.columns or '天气' not in data.columns:
            return Scatter(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        weather_mapping = {
            '晴': 1,
            '多云': 2,
            '阴': 3,
            '小雨': 4,
            '中雨': 5,
            '大雨': 6,
            '雪': 7
        }
        risk_mapping = {'低': 1, '中': 2, '高': 3}
        
        data['weather_code'] = data['天气'].map(weather_mapping).fillna(0)
        data['risk_code'] = data['风险等级'].map(risk_mapping).fillna(0)
        
        return (
            Scatter(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(data['weather_code'].tolist())
            .add_yaxis("风险等级", data['risk_code'].tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="天气与风险等级关系"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                xaxis_opts=opts.AxisOpts(name="天气类型", min_=0, max_=8,
                                        axislabel_opts=opts.LabelOpts(formatter=lambda x: 
                                            list(weather_mapping.keys())[list(weather_mapping.values()).index(int(x))] if int(x) in weather_mapping.values() else "其他")),
                yaxis_opts=opts.AxisOpts(name="风险等级", min_=0, max_=4,
                                        axislabel_opts=opts.LabelOpts(formatter=lambda x: 
                                            list(risk_mapping.keys())[list(risk_mapping.values()).index(int(x))] if int(x) in risk_mapping.values() else "无"))
            )
        )
    
    @staticmethod
    def create_operation_suggestion_distribution(data):
        """创建运营建议类型分布图"""
        if data.empty or '建议' not in data.columns:
            return Pie(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        # 统计建议类型
        suggestion_counts = {}
        for _, row in data.iterrows():
            if pd.notna(row['建议']):
                suggestions = str(row['建议']).split(';')
                for s in suggestions:
                    s = s.strip()
                    if s:
                        suggestion_counts[s] = suggestion_counts.get(s, 0) + 1
        
        suggestion_df = pd.DataFrame(list(suggestion_counts.items()), columns=['建议类型', '次数'])
        suggestion_df = suggestion_df.sort_values('次数', ascending=False).head(10)
        
        return (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add("", [list(z) for z in zip(suggestion_df['建议类型'], suggestion_df['次数'])],
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="运营建议类型分布"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="middle", pos_left="left")
            )
        )
    
    @staticmethod
    def create_weather_operation_relationship(data):
        """创建天气状况与运营建议关系图"""
        if data.empty or '天气状况' not in data.columns or '建议' not in data.columns:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        # 统计每种天气状况下的建议数量
        weather_suggestion = data.groupby('天气状况')['建议'].count().reset_index()
        weather_suggestion = weather_suggestion.sort_values('建议', ascending=False)
        
        x_data = weather_suggestion['天气状况'].tolist()
        y_data = weather_suggestion['建议'].tolist()
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("建议数量", y_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="天气状况与运营建议关系"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="建议数量"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
            )
        )
    
    @staticmethod
    def create_expected_actual_traffic_comparison(data):
        """创建预计客流量与实际客流量对比图"""
        if data.empty:
            return Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
            
        # 检查是否有预计客流量和实际客流量列
        has_expected = '预计客流量' in data.columns
        has_actual = '客流量' in data.columns
        
        # 如果没有预计客流量列，创建模拟数据
        if not has_expected:
            data['预计客流量'] = [1000 + i * 100 for i in range(len(data))]
        
        # 如果没有实际客流量列，创建模拟数据（基于预计客流量上下浮动）
        if not has_actual:
            import random
            data['客流量'] = [max(0, int(val * (0.8 + random.random() * 0.4))) for val in data['预计客流量']]
        
        # 使用前15天的数据进行对比
        sample_data = data.head(15)
        x_data = sample_data['日期'].dt.strftime('%Y-%m-%d').tolist() if '日期' in sample_data.columns else [f"第{i+1}天" for i in range(len(sample_data))]
        expected = sample_data['预计客流量'].fillna(0).tolist()
        actual = sample_data['客流量'].fillna(0).tolist()
        
        return (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="400px"))
            .add_xaxis(x_data)
            .add_yaxis("预计客流量", expected)
            .add_yaxis("实际客流量", actual)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="预计客流量与实际客流量对比"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                yaxis_opts=opts.AxisOpts(name="客流量"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
            )
        )





