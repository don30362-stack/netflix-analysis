from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests

if __package__:
    from .clean_data import REQUIRED_COLUMNS
else:
    from clean_data import REQUIRED_COLUMNS

DATA_URL = "https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "netflix_top10_raw.xlsx"


def fetch_netflix_data(
    url=DATA_URL,
    output_path=DEFAULT_OUTPUT_PATH,
):

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

    except requests.exceptions.Timeout as error:
        raise RuntimeError("下載 Netflix 資料失敗：連線逾時。") from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"下載 Netflix 資料失敗：{error}") from error

    if not response.content:
        raise RuntimeError("下載 Netflix 資料失敗：伺服器回傳空白內容。")

    try:
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
    except Exception as error:
        raise RuntimeError("下載 Netflix 資料失敗：內容不是可讀取的 Excel .xlsx 檔案。") from error

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise RuntimeError(
            f"下載 Netflix 資料失敗：Excel 缺少必要欄位：{', '.join(sorted(missing_columns))}"
        )

    output_path = Path(output_path)
    temporary_path = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # 同目錄確保在同一檔案系統；先關閉檔案以支援 Windows 替換。
        with NamedTemporaryFile(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(response.content)

        temporary_path.replace(output_path)
    except OSError as error:
        raise RuntimeError(f"儲存 Netflix 資料失敗：{output_path}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return output_path


def main():
    output_path = fetch_netflix_data()

    print("Netflix 資料下載成功")
    print(f"儲存位置：{output_path}")


if __name__ == "__main__":
    main()
