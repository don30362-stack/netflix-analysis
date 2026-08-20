from pathlib import Path

import requests

DATA_URL = "https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "netflix_top10_raw.xlsx"


def fetch_netflix_data(
    url=DATA_URL,
    output_path=DEFAULT_OUTPUT_PATH,
):

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

    except requests.exceptions.Timeout as error:
        raise RuntimeError("下載 Netflix 資料失敗：連線逾時。") from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"下載 Netflix 資料失敗：{error}") from error

    if not response.content:
        raise RuntimeError("下載 Netflix 資料失敗：伺服器回傳空白內容。")

    output_path.write_bytes(response.content)

    return output_path


def main():
    output_path = fetch_netflix_data()

    print("Netflix 資料下載成功")
    print(f"儲存位置：{output_path}")


if __name__ == "__main__":
    main()
