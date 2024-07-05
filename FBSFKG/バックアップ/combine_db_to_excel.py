import pandas as pd
import sqlite3
from datetime import datetime

def combine_databases(main_db_path, source_db_paths):
    main_conn = sqlite3.connect(main_db_path)
    main_cursor = main_conn.cursor()

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
        source_conn = sqlite3.connect(db_path)
        source_cursor = source_conn.cursor()

        source_cursor.execute("SELECT * FROM properties")
        rows = source_cursor.fetchall()

        for row in rows:
            try:
                main_cursor.execute('INSERT INTO properties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', row)
            except sqlite3.IntegrityError:
                continue

        main_conn.commit()
        source_conn.close()

    export_db_to_excel(main_conn, f"fbsfkg_all_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    main_conn.close()

def export_db_to_excel(conn, excel_filename):
    query = "SELECT * FROM properties"
    df = pd.read_sql_query(query, conn)
    df.to_excel(excel_filename, index=False, engine='openpyxl')

main_db_path = 'fbsfkg_all.db'
source_db_paths = ['fbsfkg_irisearch.db', 'fbsfkg_tenpo_innovation.db', 'fbsfkg_tenpo_smart.db']

combine_databases(main_db_path, source_db_paths)
