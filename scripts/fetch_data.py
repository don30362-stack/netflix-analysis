from pathlib import Path

import requests

url = "https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx"

# 取得專案根目錄：以當前檔案為起點，轉為絕對路徑後往上推兩層資料夾
project_root = Path(__file__).resolve().parent.parent
output_path = project_root / "data" / "raw" / "netflix_top10_raw.xlsx"

response = requests.get(url)
# 安全機制：網站掛掉、網址變更（404錯誤）或網路斷線，程式會在這裡中斷並報錯
response.raise_for_status()

output_path.write_bytes(response.content)

print("Netflix 資料下載成功")
print(f"儲存位置：{output_path}")
