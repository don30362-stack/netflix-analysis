from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "netflix_top10_raw.xlsx"

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "netflix_top10_clean.csv"

REQUIRED_COLUMNS = {
    "week",
    "category",
    "weekly_rank",
    "show_title",
    "season_title",
    "weekly_hours_viewed",
    "runtime",
    "weekly_views",
    "cumulative_weeks_in_top_10",
}


def load_raw_data(input_path=DEFAULT_INPUT_PATH):

    if not input_path.exists():
        raise FileNotFoundError(f"找不到原始資料檔案：{input_path}")

    try:
        return pd.read_excel(input_path)

    except Exception as error:
        raise RuntimeError(f"讀取原始資料失敗：{input_path}") from error


def clean_netflix_data(df):

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(f"原始資料缺少必要欄位：{', '.join(sorted(missing_columns))}")

    df = df.drop_duplicates().copy()

    df["week"] = pd.to_datetime(df["week"])

    df["season_title"] = df["season_title"].fillna("Not specified")
    # 無法轉換的數值資料統一設為 NaN
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

    # runtime 為 0 或負數不符合實際片長，視為缺失值
    df.loc[df["runtime"] <= 0, "runtime"] = pd.NA

    return df


def save_cleaned_data(
    df,
    output_path=DEFAULT_OUTPUT_PATH,
):
    # 將清洗後資料儲存為 CSV。
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
