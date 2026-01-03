import requests
import re
import csv
import time
import json
import os
import demjson3 as demjson  # 用于解析非标准 JSON 格式


def parse_weather_data(script_content):
    """从页面脚本中提取 weatherData JS数组"""
    pattern = r"const weatherData\s*=\s*(\[\{.*?\}\]);"
    match = re.search(pattern, script_content, re.DOTALL)
    if match:
        try:
            json_data = demjson.decode(match.group(1))
            return json_data
        except Exception as e:
            print("⚠️ demjson 解析失败：", e)
    return []


def split_wind(wind_str):
    """风向和风力拆分"""
    parts = wind_str.strip().split(' ')
    if len(parts) == 2:
        return parts[0], parts[1]
    return wind_str, ""


def fetch_month_data(year, month):
    url = f"http://www.tianqihoubao.com/lishi/jinzhou/month/{year}{month:02d}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    print(f"📥 正在抓取：{url}")
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        weather_json = parse_weather_data(resp.text)

        if not weather_json:
            print(f"❌ {year}年{month:02d}月 无数据或解析失败。")
            return []

        rows = []
        for item in weather_json:
            try:
                max_temp = item.get("maxTemp", "").replace("℃", "")
                min_temp = item.get("minTemp", "").replace("℃", "")
                date = item.get("date", "").strip()
                weather_day = item.get("weatherDay", "").strip()
                weather_night = item.get("weatherNight", "").strip()
                wind_day_dir, wind_day_force = split_wind(item.get("windDay", ""))
                wind_night_dir, wind_night_force = split_wind(item.get("windNight", ""))

                rows.append([
                    max_temp, min_temp, date,
                    weather_day, weather_night,
                    wind_day_dir, wind_day_force,
                    wind_night_dir, wind_night_force
                ])
            except Exception as inner_e:
                print(f"⚠️ 行解析失败：{inner_e}")
                continue

        print(f"✅ {year}年{month:02d}月 数据采集完成，共 {len(rows)} 条。")
        return rows
    except Exception as e:
        print(f"❌ {year}年{month}月 抓取失败：{e}")
        return []


def save_to_csv(rows, filename):
    headers = [
        "最高气温", "最低气温", "日期",
        "天气状况(白天)", "天气状况(夜间)",
        "风向(白天)", "风力(白天)",
        "风向(夜间)", "风力(夜间)"
    ]
    with open(filename, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"\n📁 数据保存完毕：{filename}（共 {len(rows)} 条）")


if __name__ == "__main__":
    all_data = []
    for year in range(2013, 2024):
        for month in range(1, 13):
            rows = fetch_month_data(year, month)
            if rows:
                all_data.extend(rows)
            time.sleep(2)  # 防封IP

    output_path = os.path.join(os.path.dirname(__file__), "锦州2013-2023年天气数据.csv")
    save_to_csv(all_data, output_path)
