import csv
import re
import time
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


class WebScraper:
    def __init__(self, email, password, base_url, max_pages):
        self.email = email
        self.password = password
        self.base_url = base_url
        self.max_pages = max_pages
        self.driver = None
        self.data_samples = []

    def setup_driver(self):
        options = Options()
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.maximize_window()

    def login(self, login_url):
        try:
            self.driver.get(login_url)
            self.driver.find_element(By.NAME, 'email').send_keys(self.email)
            self.driver.find_element(By.NAME, 'password').send_keys(self.password)
            self.driver.find_element(By.XPATH, "//input[@type='submit']").click()
        except Exception as e:
            print(f"ログイン中にエラーが癎りました: {e}")
            self.close_driver()
            raise

    def scrape(self):
        # スクレイピング実行日を取得

        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}&page={page}"
            self.driver.get(url)
            time.sleep(2)

            #スクレイプする親要素ごとにスクロールする
            actions = ActionChains(self.driver)
            #スクレイプする親要素名を指定する
            estate_items = self.driver.find_elements(By.CLASS_NAME, 'estateItem')

            for item in estate_items:
                actions.move_to_element(item).perform()
                time.sleep(0.5)

                property_data = self.get_property_data(item)
                if property_data:
                    self.data_samples.append(list(property_data.values()))

    def get_property_data(self, item):
        try:
            #ロード待機する要素を指定する
            image_element = WebDriverWait(item, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.estateItem__image img'))
            )
            image_src = image_element.get_attribute('src')
        except TimeoutException:
            print("画像のロード中にタイムアウトしました。")
            return None

        area_text = self.get_text(item, 'estateItem__estateArea')
        size_in_tsubo_match = re.search(r'(\d+\.\d+|\d+)坪', area_text)
        size_in_tsubo = size_in_tsubo_match.group(1) if size_in_tsubo_match else ''

        detail_link = item.find_element(By.CLASS_NAME, 'estateItem__detail').get_attribute('href')
        detail_contact = item.find_element(By.CLASS_NAME, 'estateItem__contact').get_attribute('href')

        scraping_date = datetime.now().strftime('%Y-%m-%d')

        # 賃料の処理
        rent_text = self.get_text(item, 'estateItem__estatePrice--value')
        # "ご相談"が含まれている場合は0を設定
        rent = "0" if "ご相談" in rent_text else rent_text

        return {
            "property_name": self.get_text(item, 'estateItem__estateTitle'),
            "rent":rent,        
            "rent_tax_classification": self.get_text(item, 'estateItem__estatePrice--tax'),
            "station_route": self.get_text(item, 'stationInfo__route'),
            "station_name": self.get_text(item, 'stationInfo__name--link'),
            "station_near": self.get_text(item, 'stationInfo__near--value'),
            "floor": self.get_text(item, 'estateItem__estateFloor'),
            "size_in_tsubo": size_in_tsubo,
            "address": self.get_text(item, 'estateItem__estateAddress'),
            "current_status": self.get_text(item, 'estateItem__estatePurpose--link'),
            "property_id": self.get_text(item, 'estateItem__estateId--value'),
            "property_site": "テンポスマート",
            "detail_link": detail_link,
            "detail_contact": detail_contact,
            "image_src": image_src,
            "first_published_date": scraping_date
        }

    def get_text(self, item, class_name):
        elements = item.find_elements(By.CLASS_NAME, class_name)
        if elements:
            text = elements[0].text.strip()
            if class_name == 'estateItem__estateFloor':
                return re.match(r'(.+?)階', text).group(1) if '階' in text else text
            elif class_name == 'stationInfo__near--value':
                return re.match(r'(.+?)分', text).group(1) if '分' in text else text
            elif class_name == 'stationInfo__name--link':
                return text.replace('駅', '') if text.endswith('駅') else text
            elif class_name == 'estateItem__estateAddress':
                # スペースで区切り、最初の部分のみを取得
                return text.split(' ')[0]
            else:
                return text
        return ''

    def save_to_csv(self, filename):
        headers = ["property_name", "rent", "rent_tax_classification", "station_route", "station_name", "station_near", "floor", "size_in_tsubo", "address", "current_status", "property_id", "property_site", "detail_link", "detail_contact", "image_src", "first_published_date"]
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(headers)
            for data in self.data_samples:
                csvwriter.writerow(data)

    def update_properties_table(self, c):
        # 一時テーブルからデータを取得
        c.execute('SELECT * FROM temp_properties')
        temp_properties = c.fetchall()

        for row in temp_properties:
            property_id = row[10]  # property_idの位置を適切に設定してください
            c.execute('SELECT first_published_date FROM properties WHERE property_id = ?', (property_id,))
            result = c.fetchone()

            if result is None:
                # 新規物件の場合、first_published_dateを含めて挿入
                c.execute('INSERT INTO properties VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', row)
            else:
                # 既存物件の場合、first_published_dateを除いて他のデータを更新
                update_data = row[:10] + row[11:15] + (property_id,)
                c.execute('UPDATE properties SET property_name=?, rent=?, rent_tax_classification=?, station_route=?, station_name=?, station_near=?, floor=?, size_in_tsubo=?, address=?, current_status=?, property_site=?, detail_link=?, detail_contact=?, image_src=? WHERE property_id=?', update_data)

    def save_to_db(self, db_filename):
        try:
            conn = sqlite3.connect(db_filename)
            c = conn.cursor()

            # 一時テーブルを作成（存在しない場合）
            c.execute('''CREATE TABLE IF NOT EXISTS temp_properties (
                property_name TEXT, 
                rent TEXT, 
                rent_tax_classification TEXT, 
                station_route TEXT, 
                station_name TEXT, 
                station_near TEXT, 
                floor TEXT, 
                size_in_tsubo TEXT, 
                address TEXT, 
                current_status TEXT, 
                property_id TEXT PRIMARY KEY, 
                property_site TEXT, 
                detail_link TEXT, 
                detail_contact TEXT, 
                image_src TEXT, 
                first_published_date DATE DEFAULT CURRENT_DATE
            )''')

            # 一時テーブルを空にする
            c.execute('DELETE FROM temp_properties')

            # 一時テーブルにスクレイピングしたデータを挿入
            for data in self.data_samples:
                c.execute('INSERT OR IGNORE INTO temp_properties VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)

            # メインテーブルを更新（存在しない場合は作成）
            c.execute('''CREATE TABLE IF NOT EXISTS properties (
                property_name TEXT, 
                rent TEXT, 
                rent_tax_classification TEXT, 
                station_route TEXT, 
                station_name TEXT, 
                station_near TEXT, 
                floor TEXT, 
                size_in_tsubo TEXT, 
                address TEXT, 
                current_status TEXT, 
                property_id TEXT PRIMARY KEY, 
                property_site TEXT, 
                detail_link TEXT, 
                detail_contact TEXT, 
                image_src TEXT,
                first_published_date DATE DEFAULT CURRENT_DATE
            )''')

            # update_properties_tableを呼び出し
            self.update_properties_table(c)

            # 掲載終了した物件を削除
            c.execute('''DELETE FROM properties 
                        WHERE property_id NOT IN (SELECT property_id FROM temp_properties)''')

            conn.commit()

        except sqlite3.Error as e:
            print(f"データベースへの保存中にエラーが生じました: {e}")
        finally:
            if conn:
                conn.close()

    def export_db_to_csv(self, db_filename):
        # 現在の日付を取得してファイル名を生成
        current_date = datetime.now().strftime("%Y-%m-%d")
        csv_filename_with_date = f"tenpo_smart_{current_date}.csv"

        # データベースに接続
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 全データを選択するクエリを実行
        cursor.execute("SELECT * FROM properties")
        rows = cursor.fetchall()

        # CSVファイルを開いてデータを書き込む
        with open(csv_filename_with_date, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            # CSVのヘッダーを書き込む
            csvwriter.writerow(["property_name", "rent", "rent_tax_classification", "station_route", "station_name", "station_near", "floor", "size_in_tsubo", "address", "current_status", "property_id", "property_site", "detail_link", "detail_contact", "image_src", "first_published_date"])
            # データベースから読み込んだ行をCSVに書き込む
            csvwriter.writerows(rows)

        # データベース接続を閉じる
        conn.close()

    def close_driver(self): 
        self.driver.quit()

# 使い方
load_dotenv()
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
#Web上で指定した条件で発行されるURLを指定する
base_url = "https://www.temposmart.jp/estates?parent_current_purpose%5B0%5D=159&..."

scraper = WebScraper(email, password, base_url, max_pages=26)
scraper.setup_driver()
scraper.login("https://www.temposmart.jp/login")
scraper.scrape()
scraper.save_to_db('fbsfkg_tenpo_smart.db')
scraper.export_db_to_csv('fbsfkg_tenpo_smart.db')
scraper.close_driver()