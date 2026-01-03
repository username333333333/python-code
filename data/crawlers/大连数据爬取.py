import requests
from bs4 import BeautifulSoup
import csv
import time

output_file = '大连2013-2023年天气数据.csv'

# 写入表头
with open(output_file, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        '最高气温',
        '最低气温',
        '日期',
        '天气状况(白天)',
        '天气状况(夜间)',
        '风向(白天)',
        '风力(白天)',
        '风向(夜间)',
        '风力(夜间)'
    ])

# 抓取函数
def fetch_month_data(year, month, retries=3):
    url = f"http://www.tianqihoubao.com/lishi/dalian/month/{year}{month:02d}.html"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
    }

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.encoding = 'gb2312'
            soup = BeautifulSoup(resp.text, 'html.parser')

            table = soup.find('table', class_='b')
            if table is None:
                print(f"{year}年{month:02d}月：未找到数据表格，跳过")
                return

            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                tds = row.find_all('td')
                if len(tds) != 4:
                    continue

                date_text    = tds[0].get_text().strip().replace('\r', '').replace('\n', '')
                weather_text = tds[1].get_text().strip().replace('\r', '').replace('\n', '')
                temp_text    = tds[2].get_text().strip().replace('\r', '').replace('\n', '')
                wind_text    = tds[3].get_text().strip().replace('\r', '').replace('\n', '')

                weather = [w.strip() for w in weather_text.split('/')]
                temps   = [t.strip().replace('℃', '') for t in temp_text.split('/')]
                winds   = [w.strip() for w in wind_text.split('/')]

                if len(weather)==2 and len(temps)==2 and len(winds)==2:
                    parts_day   = winds[0].split()
                    parts_night = winds[1].split()

                    if len(parts_day)==2 and len(parts_night)==2:
                        row_data = [
                            temps[1],          # 最高气温
                            temps[0],          # 最低气温
                            date_text,         # 日期
                            weather[0],        # 天气(白天)
                            weather[1],        # 天气(夜间)
                            parts_day[0],      # 风向(白天)
                            parts_day[1],      # 风力(白天)
                            parts_night[0],    # 风向(夜间)
                            parts_night[1],    # 风力(夜间)
                        ]
                        with open(output_file, mode='a', encoding='utf-8', newline='') as f:
                            csv.writer(f).writerow(row_data)

            print(f"{year}年{month:02d}月 数据采集完成。")
            time.sleep(3)  # 避免被封，适当延时
            return

        except Exception as e:
            print(f"抓取失败：{url}，错误：{e}")
            if attempt < retries - 1:
                print(f"重试中（第 {attempt+2} 次）...")
                time.sleep(5)
            else:
                print(f"{year}年{month:02d}月 最终失败，跳过。")

# 主程序：2013-2023年
for year in range(2013, 2024):
    for month in range(1, 13):
        fetch_month_data(year, month)
