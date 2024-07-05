from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import csv
import time

# 環境変数からメールアドレスとパスワードを取得
email = "let.smakeawish1230@gmail.com"
password = "gs5T76aAR3R3X"

# WebDriverの設定
options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# ログインページにアクセス
driver.get("https://www.temposmart.jp/login")

# メールアドレスとパスワードを入力
email_input = driver.find_element(By.NAME, 'email')
email_input.send_keys(email)
password_input = driver.find_element(By.NAME, 'password')
password_input.send_keys(password)

# ログインボタンをクリック
login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
login_button.click()

# 基本URL
base_url = "https://www.temposmart.jp/estates?parent_current_purpose%5B0%5D=159&child_current_purpose%5B0%5D=180&child_current_purpose%5B1%5D=183&child_current_purpose%5B2%5D=188&child_current_purpose%5B3%5D=194&child_current_purpose%5B4%5D=198&child_current_purpose%5B5%5D=209&child_current_purpose%5B6%5D=221&child_current_purpose%5B7%5D=225&child_current_purpose%5B8%5D=230&child_current_purpose%5B9%5D=250&child_current_purpose%5B10%5D=256&child_current_purpose%5B11%5D=258&child_current_purpose%5B12%5D=160&child_current_purpose%5B13%5D=164&child_current_purpose%5B14%5D=166&child_current_purpose%5B15%5D=170"

# 最大ページ数を設定
max_pages = 10  # 最大ページ数は必要に応じて調整してください

for page in range(1, max_pages + 1):
    # 特定のページに移動    
    url = f"{base_url}&page={page}"
    driver.get(url)
    time.sleep(2)

    try:
        # `ul`要素の存在を確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "estatesMain__estateList--ul"))
        )

        # 特定数の`li`要素の存在を確認
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "estatesMain__estateList--li")) >= 50
        )

        # 特定の`li`要素内の画像がロードされるのを待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='estatesMain__estateList--li'][1]//img"))
        )
    except TimeoutException as e:
        print("エラーが発生しました:", e)
        # 必要に応じてさらなるエラー処理を行う

    estate_items = driver.find_elements(By.CLASS_NAME, 'estateItem')

    for item in estate_items:
        # 建物情報の取得
        property_name = item.find_element(By.CLASS_NAME, 'estateItem__estateTitle').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estateTitle')) > 0 else ''
        rent = item.find_element(By.CLASS_NAME, 'estateItem__estatePrice--value').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estatePrice--value')) > 0 else ''
        rent_tax_classification = item.find_element(By.CLASS_NAME, 'estateItem__estatePrice--tax').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estatePrice--tax')) > 0 else ''
        station_route = item.find_element(By.CLASS_NAME, 'stationInfo__route').text.strip() if len(item.find_elements(By.CLASS_NAME, 'stationInfo__route')) > 0 else ''
        station_name = item.find_element(By.CLASS_NAME, 'stationInfo__name--link').text.strip() if len(item.find_elements(By.CLASS_NAME, 'stationInfo__name--link')) > 0 else ''
        station_near = item.find_element(By.CLASS_NAME, 'stationInfo__near--value').text.strip() if len(item.find_elements(By.CLASS_NAME, 'stationInfo__near--value')) > 0 else ''
        floor = item.find_element(By.CLASS_NAME, 'estateItem__estateFloor').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estateFloor')) > 0 else ''
        # 面積（坪）の取得
        area_text = item.find_element(By.CLASS_NAME, 'estateItem__estateArea').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estateArea')) > 0 else ''
        size_in_tsubo_match = re.search(r'(\d+\.\d+|\d+)坪', area_text)
        size_in_tsubo = size_in_tsubo_match.group(1) if size_in_tsubo_match else ''
        address = item.find_element(By.CLASS_NAME, 'estateItem__estateAddress').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estateAddress')) > 0 else ''
        current_status = item.find_element(By.CLASS_NAME, 'estateItem__estatePurpose--link').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estatePurpose--link')) > 0 else ''
        # 詳細ページのリンクを取得
        detail_link_element = item.find_element(By.CLASS_NAME, 'estateItem__detail')
        detail_link = detail_link_element.get_attribute('href')
        # 詳細ページのリンクを取得
        detail_link_contact = item.find_element(By.CLASS_NAME, 'estateItem__contact')
        detail_contact = detail_link_element.get_attribute('href')
        property_id = item.find_element(By.CLASS_NAME, 'estateItem__estateId--value').text.strip() if len(item.find_elements(By.CLASS_NAME, 'estateItem__estateId--value')) > 0 else ''
        property_site = "テンポスマート"
        # 画像URLの取得
        image_element = item.find_element(By.CSS_SELECTOR, '.estateItem__image img')
        image_src = image_element.get_attribute('src')

        # 各項目をリストに追加
        data_sample = [property_name, rent, rent_tax_classification, station_route, station_name, station_near,floor, size_in_tsubo, address, current_status, detail_link, detail_contact, property_id, property_site, image_src]

# CSVファイルにデータを書き込む
csv_filename = 'temposmart_data.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(headers)  # ヘッダー行を書き込む
    for data in data_samples:
        csvwriter.writerow(data)

driver.quit()  # WebDriverを終了

# ブラウザを閉じる
driver.quit()
