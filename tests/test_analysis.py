import pandas as pd

from scripts.analyze_data import (
    build_consecutive_segments,
    calculate_segment_correlations,
    load_data,
)

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

EXPECTED_CATEGORIES = {
    "Films (English)",
    "Films (Non-English)",
    "TV (English)",
    "TV (Non-English)",
}


def test_data_quality():
    # 檢查正式清洗資料的結構與基本品質。

    df = load_data()

    # 1. DataFrame 不可為空
    assert not df.empty, "分析資料不可為空"

    # 2. 正式資料的 9 個欄位都必須存在
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    assert not missing_columns, f"分析資料缺少必要欄位：{sorted(missing_columns)}"

    # 3. 清洗後不應存在完全重複資料
    assert not df.duplicated().any(), "清洗後資料不應包含完全重複資料"

    # 4. 關鍵欄位不可有缺失值
    columns_without_missing_values = [
        "week",
        "category",
        "weekly_rank",
        "show_title",
        "season_title",
        "weekly_hours_viewed",
        "cumulative_weeks_in_top_10",
    ]

    for column in columns_without_missing_values:
        assert df[column].notna().all(), f"{column} 不應包含缺失值"

    # runtime 與 weekly_views 在較早期官方資料中本來就有缺失，
    # 因此只確認目前資料中確實存在有效值
    assert df["runtime"].notna().any(), "runtime 應至少存在部分有效資料"

    assert df["weekly_views"].notna().any(), "weekly_views 應至少存在部分有效資料"

    # 5. week 應為日期型態
    assert pd.api.types.is_datetime64_any_dtype(df["week"]), "week 應為日期型態"

    # 6. weekly_rank 應介於 1～10
    assert df["weekly_rank"].between(1, 10).all(), "weekly_rank 必須介於 1 到 10"

    # 7. 數值欄位必須符合合理範圍
    assert (df["weekly_hours_viewed"] >= 0).all(), "weekly_hours_viewed 不應出現負值"

    assert (df["weekly_views"].dropna() >= 0).all(), "weekly_views 不應出現負值"

    assert (df["runtime"].dropna() > 0).all(), "runtime 有效資料應大於 0"

    assert (df["cumulative_weeks_in_top_10"] >= 1).all(), (
        "cumulative_weeks_in_top_10 應至少為 1"
    )

    # 8. category 應只有 Netflix 官方四種類別
    unexpected_categories = set(df["category"].unique()) - EXPECTED_CATEGORIES

    assert not unexpected_categories, (
        f"發現非預期 category：{sorted(unexpected_categories)}"
    )


def test_consecutive_segments():
    # 檢查連續上榜區段的切分與主分析條件。

    df = load_data()

    correlation_data = build_consecutive_segments(df)

    assert not correlation_data.empty, "連續上榜分析資料不可為空"

    # 9. 同一連續區段內相鄰日期必須剛好相隔 7 天
    date_differences = (
        correlation_data.sort_values(
            [
                "analysis_unit",
                "streak_id",
                "week",
            ]
        )
        .groupby(
            [
                "analysis_unit",
                "streak_id",
            ]
        )["week"]
        .diff()
        .dt.days.dropna()
    )

    assert (date_differences == 7).all(), "同一連續上榜區段內，相鄰週期必須相隔 7 天"

    # streak_week 在每個區段內應從 1 開始連續增加
    for _, group in correlation_data.groupby(["analysis_unit", "streak_id"]):
        expected_weeks = list(range(1, len(group) + 1))
        actual_weeks = group.sort_values("week")["streak_week"].tolist()

        assert actual_weeks == expected_weeks, "streak_week 應從 1 開始連續增加"

    # 主分析設定：至少連續上榜 5 週
    segment_results = calculate_segment_correlations(
        correlation_data,
        minimum_weeks=5,
    )

    assert not segment_results.empty, "應至少存在一個符合主分析條件的有效區段"

    assert (segment_results["weeks"] >= 5).all(), "主分析區段長度必須至少為 5 週"

    # Pearson / Spearman 合法範圍
    assert segment_results["pearson"].between(-1, 1).all(), (
        "Pearson 相關係數必須介於 -1 到 1"
    )

    assert segment_results["spearman"].between(-1, 1).all(), (
        "Spearman 相關係數必須介於 -1 到 1"
    )


def test_correlation_function():
    # 利用答案已知的小型資料測試相關性計算函式。

    test_data = pd.DataFrame(
        {
            "analysis_unit": ["Test Show"] * 5,
            "streak_id": [1] * 5,
            "category": ["TV (English)"] * 5,
            "show_title": ["Test Show"] * 5,
            "season_title": ["Season 1"] * 5,
            "streak_week": [1, 2, 3, 4, 5],
            "weekly_views": [
                500,
                400,
                300,
                200,
                100,
            ],
        }
    )

    result = calculate_segment_correlations(
        test_data,
        minimum_weeks=5,
    )

    # 固定測試資料只有一個有效區段
    assert len(result) == 1, "固定測試資料應產生 1 個有效區段"

    pearson = result.iloc[0]["pearson"]
    spearman = result.iloc[0]["spearman"]

    assert -1 <= pearson <= 1, "Pearson 相關係數超出合法範圍"

    assert -1 <= spearman <= 1, "Spearman 相關係數超出合法範圍"

    # streak_week 完全增加、weekly_views 完全下降，
    # 因此 Pearson 與 Spearman 都應為 -1
    assert abs(pearson + 1) < 1e-10, "完全遞減資料的 Pearson 應為 -1"

    assert abs(spearman + 1) < 1e-10, "完全遞減資料的 Spearman 應為 -1"


def main():
    test_data_quality()
    print("✓ 資料品質測試通過")

    test_consecutive_segments()
    print("✓ 連續上榜區段測試通過")

    test_correlation_function()
    print("✓ 相關性函式測試通過")

    print("\n===== 所有基本測試通過 =====")


if __name__ == "__main__":
    main()
