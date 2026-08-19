from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent
default_input_path = project_root / "data" / "raw" / "netflix_top10_raw.xlsx"

default_output_path = project_root / "data" / "processed" / "netflix_top10_clean.csv"


def load_raw_data(input_path=default_input_path):

    return pd.read_excel(input_path)


def clean_netflix_data(df):

    df = df.drop_duplicates().copy()

    df["week"] = pd.to_datetime(df["week"])

    df["season_title"] = df["season_title"].fillna("Not specified")
    # 將欄位轉換為數字型態，若遇到無法轉換的文字則強迫變更為 NaN 空值，避免程式崩潰
    numeric_columns = [
        "weekly_rank",
        "weekly_hours_viewed",
        "runtime",
        "weekly_views",
        "cumulative_weeks_in_top_10",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def save_cleaned_data(
    df,
    output_path=default_output_path,
):
    """將清洗後資料儲存為 CSV。"""
    # 建立已處理資料的儲存目錄（若已存在則忽略，不存在則連同父目錄一起建立）
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    # 匯出為 CSV 檔：使用 utf-8-sig 編碼防止 Excel 開啟時產生亂碼
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    return output_path


def main():
    df = load_raw_data()

    df = clean_netflix_data(df)

    output_path = save_cleaned_data(df)

    print("\n資料清洗完成")
    print(f"清洗後資料筆數：{len(df)}")
    print(f"輸出位置：{output_path}")


if __name__ == "__main__":
    main()
