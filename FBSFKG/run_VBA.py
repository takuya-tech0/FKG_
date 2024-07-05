import win32com.client

def run_vba_macro():
    # Excelアプリケーションを起動
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True  # Excelを表示する場合はTrueに設定
    
    # ワークブックを開く    
    workbook_path = r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\SharepointUP.xlsm"  # 実行したいVBAマクロを含むExcelファイルのパス
    workbook = excel.Workbooks.Open(workbook_path)
    
    # VBAマクロを実行
    macro_name = "SaveWorkbook"  # 実行したいマクロの名前を設定
    excel.Application.Run(f"'{workbook.Name}'!{macro_name}")
    
    # ワークブックを保存して閉じる
    workbook.Close(SaveChanges=True)
    excel.Quit()

if __name__ == "__main__":
    run_vba_macro()
