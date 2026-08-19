from pathlib import Path

import requests


DATA_URL = "https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx"

project_root = Path(__file__).resolve().parent.parent
default_output_path = project_root / "data" / "raw" / "netflix_top10_raw.xlsx"


def fetch_netflix_data(
    url=DATA_URL,
    output_path=default_output_path,
):
    """下載 Netflix Top 10 原始資料並儲存為 Excel。"""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=30)

    # 網站錯誤、網址失效或其他 HTTP 錯誤時直接中止
    response.raise_for_status()

    output_path.write_bytes(response.content)

    return output_path


def main():
    output_path = fetch_netflix_data()

    print("Netflix 資料下載成功")
    print(f"儲存位置：{output_path}")


if __name__ == "__main__":
    main()
