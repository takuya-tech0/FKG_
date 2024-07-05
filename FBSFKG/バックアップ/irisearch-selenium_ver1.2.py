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
from selenium.common.exceptions import NoSuchElementException

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

            # クッキー同意のボタンが存在するかチェックし、存在すればクリック
            try:
                cookie_agree_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".cookie-agree"))
                )
                cookie_agree_button.click()
            except TimeoutException:
                print("クッキー同意のポップアップが見つかりません。")

            # メールアドレスとパスワードを入力
            self.driver.find_element(By.NAME, 'data[AuthMember][mail_address]').send_keys(self.email)
            self.driver.find_element(By.NAME, 'data[AuthMember][password]').send_keys(self.password)

            # ログインボタンをクリック
            login_button = self.driver.find_element(By.XPATH, "//input[@type='image'][@alt='ログイン']")
            login_button.click()
            time.sleep(5)
        except Exception as e:
            print(f"ログイン中にエラーが発生しました: {e}")
            self.close_driver()
            raise

    def scrape(self):
        # スクレイピング実行日を取得

        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}&hotlist={page}"
            self.driver.get(url)

            #スクレイプする親要素ごとにスクロールする
            actions = ActionChains(self.driver)
            #スクレイプする親要素名を指定する
            estate_items = self.driver.find_elements(By.XPATH, '//table[@summary="物件詳細1"]')
            print(len(estate_items))  # ここで選択された要素の数を印刷

            for item in estate_items:
                actions.move_to_element(item).perform()
                time.sleep(0.5)

                property_data = self.get_property_data(item)
                if property_data:
                    self.data_samples.append(list(property_data.values()))

    def get_property_data(self, item):
        try:
            # 物件名称
            try:
                property_name_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[1]")
                property_name_full_text = property_name_element.text
                # 「&」が含まれている場合は、その前の部分を取り出す
                if '&' in property_name_full_text:
                    property_name = property_name_full_text.split('&')[0].strip()
                else:
                    property_name = property_name_full_text.strip()
            except NoSuchElementException:
                print("物件名称の要素が見つかりません。")
                property_name = ""

            # 賃料
            try:
                rent_element = item.find_element(By.XPATH, ".//th[text()='賃料']/following-sibling::td/span[@class='b_red']")
                rent = rent_element.text.strip()
            except NoSuchElementException:
                print("賃料の要素が見つかりません。")
                rent = "0"

            # 沿線
            try:
                station_route_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[5]/td")
                station_route = station_route_element.text.split()[0].strip()
            except NoSuchElementException:
                print("沿線の要素が見つかりません。")
                station_route = ""

            # 駅名
            try:
                station_name_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[5]/td")
                station_name = station_name_element.text.replace('駅', '').strip()
            except NoSuchElementException:
                print("駅名の要素が見つかりません。")
                station_name = ""

            # 徒歩
            try:
                station_info_text = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[5]/td").text
                station_near_match = re.search(r'徒歩(\d+)分', station_info_text)
                if station_near_match:
                    station_near = station_near_match.group(1)
                else:
                    station_near = ""
            except NoSuchElementException:
                print("徒歩の要素が見つかりません。")
                station_near = ""

            # 階数
            try:
                floor_text = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[7]/td[1]").text
                floor = floor_text.split('&')[0].strip() if '&' in floor_text else floor_text.strip()
            except NoSuchElementException:
                print("階数の要素が見つかりません。")
                floor = ""

            # 坪数
            try:
                size_in_tsubo_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[4]/td[2]/span")
                size_in_tsubo = size_in_tsubo_element.text.strip()  # .textを使用してテキスト内容を取得
            except NoSuchElementException:
                print("坪数の要素が見つかりません。")
                size_in_tsubo = ""

            # 住所
            try:
                address_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[6]/td")
                address = address_element.text.split('&')[0].strip()
            except NoSuchElementException:
                address = ""

            # 現況
            try:
                current_status_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[3]/td[2]")
                current_status = current_status_element.text.split('&')[0].strip()
            except NoSuchElementException:
                print("現況の要素が見つかりません。")
                current_status = ""

            # 物件ID
            try:
                property_id_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[2]/table/tbody/tr[1]/td")
                property_id = property_id_element.text.strip()
            except NoSuchElementException:
                print("物件IDの要素が見つかりません。")
                property_id = ""

            # 物件リンク
            try:
                detail_link_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[3]/td/a")
                detail_link = "https://www.iri-search.net" + detail_link_element.get_attribute('href')
            except NoSuchElementException:
                print("物件リンクの要素が見つかりません。")
                detail_link = ""

            # 画像リンク
            try:
                image_element = item.find_element(By.XPATH, "//*[@id='search_result']/table[1]/tbody/tr[2]/td[1]/div/a[1]/img")
                image_src = "https://www.iri-search.net" + image_element.get_attribute('src')
            except NoSuchElementException:
                print("画像リンクの要素が見つかりません。")
                image_src = ""

            scraping_date = datetime.now().strftime('%Y-%m-%d')

            return {
                "property_name": property_name,
                "rent": rent,
                "rent_tax_classification": "税込",
                "station_route": station_route,
                "station_name": station_name,
                "station_near": station_near,
                "floor": floor,
                "size_in_tsubo": size_in_tsubo,
                "address": address,
                "current_status": current_status,
                "property_id": property_id,
                "property_site": "イリサーチ",
                "detail_link": detail_link,
                "detail_contact": "詳細リンクより問い合わせください",
                "image_src": image_src,
                "first_published_date": scraping_date
            }
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return None

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

    def export_db_to_csv(self, db_filename, csv_filename):
        # データベースに接続
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 全データを選択するクエリを実行
        cursor.execute("SELECT * FROM properties")
        rows = cursor.fetchall()

        # CSVファイルを開いてデータを書き込む
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
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
base_url = "https://www.iri-search.net/estate_search/index?page_start_num=0&area_code=1&prefectural_code=13&contract_confirm[]=31&order_by=6"

scraper = WebScraper(email, password, base_url, max_pages=1)
scraper.setup_driver()
scraper.login("https://www.iri-search.net/pages/login/")
scraper.scrape()
scraper.save_to_db('fbsfkg.db')
scraper.export_db_to_csv('fbsfkg.db', 'exported_data.csv')
scraper.close_driver()