from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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

# 検索結果が読み込まれるまで待機（必要に応じて）
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "someElementOnResultsPage"))  # 検索結果ページ上の要素ID
)

# 検索結果が読み込まれるまで待機（必要に応じて）
time.sleep(2)

# 必要な処理を実行...

# ブラウザを閉じる
driver.quit()
