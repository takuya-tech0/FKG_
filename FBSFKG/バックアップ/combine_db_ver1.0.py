import csv
import sqlite3
from datetime import datetime

def combine_databases(main_db_path, source_db_paths):
    # メインデータベースに接続
    main_conn = sqlite3.connect(main_db_path)
    main_cursor = main_conn.cursor()

    # メインデータベース内のテーブルを準備（存在しない場合）
    main_cursor.execute('''CREATE TABLE IF NOT EXISTS properties (
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
                            first_published_date DATE)''')
    main_conn.commit()

    for db_path in source_db_paths:
        # 各ソースデータベースに接続
        source_conn = sqlite3.connect(db_path)
        source_cursor = source_conn.cursor()

        # ソースデータベースからデータを読み込み
        source_cursor.execute("SELECT * FROM properties")
        rows = source_cursor.fetchall()

        # メインデータベースにデータを挿入（既存データはスキップする例）
        for row in rows:
            try:
                main_cursor.execute('INSERT INTO properties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', row)
            except sqlite3.IntegrityError:
                # 重複するproperty_idがある場合はスキップ（または必要に応じて更新処理を行う）
                continue

        # 変更をコミット
        main_conn.commit()

        # ソースデータベース接続を閉じる
        source_conn.close()

    # 結合後のデータベースからCSVにエクスポート
    export_db_to_csv(main_conn, f"fbsfkg_all_{datetime.now().strftime('%Y-%m-%d')}.csv")
    export_db_to_csv(main_conn, f"fbsfkg_all.csv")

    # メインデータベース接続を閉じる
    main_conn.close()

def export_db_to_csv(conn, csv_filename):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties")
    rows = cursor.fetchall()
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["property_name", "rent", "rent_tax_classification", "station_route", "station_name", "station_near", "floor", "size_in_tsubo", "address", "current_status", "property_id", "property_site", "detail_link", "detail_contact", "image_src", "first_published_date"])
        csvwriter.writerows(rows)

# メインデータベースとソースデータベースのパス
main_db_path = 'fbsfkg_all.db'
source_db_paths = ['fbsfkg_irisearch.db', 'fbsfkg_tenpo_innovation.db', 'fbsfkg_tenpo_smart.db']

# データベース結合処理の実行
combine_databases(main_db_path, source_db_paths)