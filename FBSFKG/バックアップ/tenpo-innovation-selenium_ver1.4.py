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
            self.driver.find_element(By.NAME, 'email').send_keys(self.email)
            self.driver.find_element(By.NAME, 'password').send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        except Exception as e:
            print(f"ログイン中にエラーが癎りました: {e}")
            self.close_driver()
            raise

    def scrape(self):
        detail_links =  self.collect_detail_links()
        self.scrape_details(detail_links)

    def collect_detail_links(self):
        detail_links = []

        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}{page}"
            self.driver.get(url)
            time.sleep(2)  # 動的なコンテンツの読み込み待ち

            estate_items = self.driver.find_elements(By.CLASS_NAME, 'c-propertyList__item')
            for item in estate_items:
                relative_link = item.find_element(By.CLASS_NAME, 'js-link').get_attribute('href')
                # ベースURLと相対URLを結合して詳細ページの完全なURLを作成
                detail_link = "https://www.i-tenpo.com/" + relative_link
                detail_links.append(detail_link)

        return detail_links

    def scrape_details(self, detail_links):
        for link in detail_links:
            self.driver.get(link)
            # 詳細ページからデータを取得する
            property_data = self.get_property_data()  # item 引数を渡さない
            if property_data:
                self.data_samples.append(property_data)
            time.sleep(1)

    def get_property_data(self):

        try:
            # 物件名称
            try:
                property_name_element = self.driver.find_element(By.XPATH, "//div[@class='p-propertyDetail__main__info__main__item__ttl'][contains(text(), '建物名')]/following-sibling::div[@class='p-propertyDetail__main__info__main__item__text']/p")
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
                rent_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__main__item__ttl') and contains(text(), '賃料')]/following-sibling::div[contains(@class, 'p-propertyDetail__main__info__main__item__text')]/p/span")
                rent = rent_element.text.strip()
            except NoSuchElementException:
                print("賃料の要素が見つかりません。")
                rent = "0"

            try:
                station_route_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__main__item__text station')]/a[1]")
                # 「／」で分割して最初の部分（沿線名）のみを取り出す
                station_route = station_route_element.text.strip()
            except NoSuchElementException:
                print("沿線の要素が見つかりません。")
                station_route = ""  

            # 駅名
            try:
                station_name_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__main__item__text station')]/a[2]")
                station_name = station_name_element.text.strip()
                if station_name.endswith("駅"):
                    station_name = station_name[:-1]  # 末尾の"駅"を除去
            except NoSuchElementException:
                print("駅名の要素が見つかりません。")
                station_name = ""

            # 徒歩（<span>タグ内のテキストを取得）
            try:
                # XPathを使って<span>タグのテキストを直接取得
                station_walk_time_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__main__item__text station')]/p/span")
                station_walk_time = station_walk_time_element.text.strip()  # .textでテキスト内容を取得
                # 徒歩の時間を取得（例: "3"）
                station_near = station_walk_time
            except NoSuchElementException:
                print("徒歩の要素が見つかりません。")
                station_near = ""

            # 階数
            try:
                floor_text = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__sub__item__ttl') and contains(text(), '階層')]/following-sibling::div[contains(@class, 'p-propertyDetail__main__info__sub__item__text')]").text
                floor = floor_text.split('&')[0].strip() if '&' in floor_text else floor_text.strip()
            except NoSuchElementException:
                print("階数の要素が見つかりません。")
                floor = ""

            # 坪数
            try:
                size_in_tsubo_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__sub__item__ttl') and contains(text(), '面積')]/following-sibling::div[contains(@class, 'p-propertyDetail__main__info__sub__item__text')]")
                size_in_tsubo_text = size_in_tsubo_element.text.strip()  # .textを使用してテキスト内容を取得
                # 正規表現で括弧内の数値を抽出
                match = re.search(r"\((\d+\.\d+|\d+)坪\)", size_in_tsubo_text)
                if match:
                    size_in_tsubo = match.group(1)  # 括弧内の数値部分
                else:
                    size_in_tsubo = ""
            except NoSuchElementException:
                print("坪数の要素が見つかりません。")
                size_in_tsubo = ""

            # 住所
            try:
                address_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__main__item__text') and contains(@class, 'p-propertyDetail__main__info__main__item__text--aria')]")
                # 住所として表示される全テキストを取得
                full_address_text = address_element.text.strip()
                # 不要な部分（例えば、「地図表示」などのリンクテキスト）を削除
                # ここでは単純化のために具体的な処理は示していませんが、
                # 正規表現や文字列の分割などを用いて必要な部分のみを抽出します
                address = full_address_text.split('地図表示')[0].strip()
            except NoSuchElementException:
                address = ""

            # 現況
            try:
                current_status_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetail__main__info__sub__item__ttl') and contains(text(), '現業態')]/following-sibling::div[contains(@class, 'p-propertyDetail__main__info__sub__item__text')]/a")
                current_status = current_status_element.text.strip()
            except NoSuchElementException:
                print("現況の要素が見つかりません。")
                current_status = ""

            # 物件ID
            try:
                property_id_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-propertyDetailTel__sub')]/p[2]")
                property_id_text = property_id_element.text.strip()
                # "物件No："を空文字列に置換して除去
                property_id = property_id_text.replace("物件No：", "")
            except NoSuchElementException:
                print("物件IDの要素が見つかりません。")
                property_id = ""

            # 物件リンク
            property_link = self.driver.current_url

            # 画像リンク
            try:
                image_element = self.driver.find_element(By.XPATH, "/html/body/div/main/form/div/div[1]/section[1]/div[1]/div[1]/ul/li[1]/a/img")
                image_src = image_element.get_attribute('src')
            except NoSuchElementException:
                print("画像リンクの要素が見つかりません。")
                image_src = ""

            scraping_date = datetime.now().strftime('%Y-%m-%d')

            return {
                "property_name": property_name,
                "rent": rent,
                "rent_tax_classification": "税抜",
                "station_route": station_route,
                "station_name": station_name,
                "station_near": station_near,
                "floor": floor,
                "size_in_tsubo": size_in_tsubo,
                "address": address,
                "current_status": current_status,
                "property_id": property_id,
                "property_site": "テンポイノベーション",
                "detail_link": property_link,
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
            for data_dict in self.data_samples:
                data_tuple = (
                    data_dict["property_name"],
                    data_dict["rent"],
                    data_dict["rent_tax_classification"],
                    data_dict["station_route"],
                    data_dict["station_name"],
                    data_dict["station_near"],
                    data_dict["floor"],
                    data_dict["size_in_tsubo"],
                    data_dict["address"],
                    data_dict["current_status"],
                    data_dict["property_id"],
                    data_dict["property_site"],
                    data_dict["detail_link"],
                    data_dict["detail_contact"],
                    data_dict["image_src"],
                    data_dict["first_published_date"],
                )
                c.execute('INSERT OR IGNORE INTO temp_properties VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_tuple)

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
        csv_filename_with_date = f"exported_data_{current_date}.csv"

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
base_url = "https://www.i-tenpo.com/new-list/?page="
scraper = WebScraper(email, password, base_url, max_pages=3)
scraper.setup_driver()
scraper.login("https://www.i-tenpo.com/mypage/login")
scraper.scrape()
scraper.save_to_db('fbsfkg_tenpo_innovation.db')
scraper.export_db_to_csv('fbsfkg_tenpo_innovation.db')
scraper.close_driver()