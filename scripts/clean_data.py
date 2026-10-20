from pathlib import Path

import numpy as np
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
        raise ValueError(
            f"原始資料缺少必要欄位（{len(missing_columns)} 個）："
            f"{', '.join(sorted(missing_columns))}"
        )

    if df.empty:
        raise ValueError("原始資料不可為空：0 筆。")

    df = df.drop_duplicates().copy()
    errors = []

    df["week"] = pd.to_datetime(df["week"], errors="coerce")

    df["season_title"] = df["season_title"].fillna("Not specified")
    # 原本的缺值保留；非空內容轉換失敗必須回報，不能偽裝成合法缺值。
    numeric_columns = [
        "weekly_rank",
        "weekly_hours_viewed",
        "runtime",
        "weekly_views",
        "cumulative_weeks_in_top_10",
    ]

    for column in numeric_columns:
        original = df[column]
        df[column] = pd.to_numeric(
            original,
            errors="coerce",
        )
        invalid_count = int((original.notna() & df[column].isna()).sum())
        if invalid_count:
            errors.append(f"{column} 無法轉為數值：{invalid_count} 筆")
        infinite_count = int((df[column].notna() & ~np.isfinite(df[column])).sum())
        if infinite_count:
            errors.append(f"{column} 必須是有限數值：{infinite_count} 筆")

    for column in [
        "week", "category", "weekly_rank", "show_title",
        "weekly_hours_viewed", "cumulative_weeks_in_top_10",
    ]:
        missing = df[column].isna()
        if column in ["category", "show_title"]:
            missing = missing | df[column].astype("string").str.strip().eq("").fillna(False)
        if missing.any():
            label = "缺失或無法解析日期" if column == "week" else "缺少有效關鍵值"
            errors.append(f"{column} {label}：{int(missing.sum())} 筆")

    expected_categories = {
        "Films (English)", "Films (Non-English)",
        "TV (English)", "TV (Non-English)",
    }
    invalid_category = df["category"].notna() & ~df["category"].isin(expected_categories)
    if invalid_category.any():
        errors.append(f"category 不屬於官方四種類別：{int(invalid_category.sum())} 筆")

    for column in ["weekly_rank", "cumulative_weeks_in_top_10"]:
        values = df.loc[df[column].notna() & np.isfinite(df[column]), column]
        invalid = (values < 1) | (values % 1 != 0)
        if column == "weekly_rank":
            invalid = invalid | (values > 10)
        if invalid.any():
            rule = "1～10 的整數" if column == "weekly_rank" else "大於等於 1 的整數"
            errors.append(f"{column} 必須是{rule}：{int(invalid.sum())} 筆")

    for column in ["weekly_hours_viewed", "weekly_views"]:
        invalid = df[column] < 0
        if invalid.any():
            errors.append(f"{column} 不得為負值：{int(invalid.sum())} 筆")

    for keys, label in [
        (["week", "category", "weekly_rank"], "同週同類別排名衝突"),
        (["week", "category", "show_title", "season_title"], "同週同類別作品及季度重複"),
    ]:
        duplicate = df.duplicated(subset=keys, keep=False)
        if duplicate.any():
            groups = len(df.loc[duplicate, keys].drop_duplicates())
            errors.append(f"{label}：{groups} 組，涉及 {int(duplicate.sum())} 筆")

    if errors:
        raise ValueError("資料驗證失敗：\n" + "\n".join(errors))

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
