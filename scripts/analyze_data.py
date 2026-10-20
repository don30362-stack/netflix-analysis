from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "netflix_top10_clean.csv"


def load_data(input_path=DEFAULT_INPUT_PATH):
    # 讀取清洗後的 Netflix Top 10 資料。

    df = pd.read_csv(input_path)
    df["week"] = pd.to_datetime(df["week"])

    return df


def add_analysis_columns(df):
    # 建立電影 / 影集與英語 / 非英語分析欄位。

    df = df.copy()

    df["content_type"] = df["category"].apply(
        lambda x: "Films" if x.startswith("Films") else "TV"
    )

    df["language_type"] = df["category"].apply(
        lambda x: "Non-English" if "Non-English" in x else "English"
    )

    return df


# =========================
# 1. 電影與影集熱門程度比較
# =========================
def analyze_content_type(df):
    # 計算電影與影集平均每週觀看次數。

    views_df = df.dropna(subset=["weekly_views"]).copy()

    result = (
        views_df.groupby("content_type")["weekly_views"].mean().reindex(["Films", "TV"])
    )

    return result


# =========================
# 2. 英語與非英語內容比較
# =========================
def analyze_language(df):
    # 比較電影與影集中英語、非英語內容的平均每週觀看次數。

    views_df = df.dropna(subset=["weekly_views"]).copy()

    result = (
        views_df.groupby(["content_type", "language_type"])["weekly_views"]
        .mean()
        .unstack()
        .reindex(
            index=["Films", "TV"],
            columns=["English", "Non-English"],
        )
    )

    return result


# =========================
# 3. Top 10 停留最久作品
# =========================
def analyze_top_titles(df, top_n=10):
    """依公開上榜項目標籤取最大累積週數；三欄並非官方唯一作品 ID。"""

    result = (
        df.groupby(
            ["category", "show_title", "season_title"], as_index=False, dropna=False
        )["cumulative_weeks_in_top_10"]
        .max()
        .sort_values(
            ["cumulative_weeks_in_top_10", "show_title", "category", "season_title"],
            ascending=[False, True, True, True],
            na_position="last",
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return result


# =========================
# 4. 每週總觀看時數趨勢
# =========================
def analyze_weekly_trend(df):
    # 分析 Netflix Top 10 整體每週觀看時數趨勢。

    weekly_total_hours = (
        df.groupby("week")["weekly_hours_viewed"].sum(min_count=1).sort_index()
    )
    if not weekly_total_hours.notna().any():
        raise ValueError(
            f"每週觀看時數皆缺失，無法分析趨勢：{len(weekly_total_hours)} 週有效值為 0 筆。"
        )

    max_week = weekly_total_hours.idxmax()
    max_hours = weekly_total_hours.max()

    min_week = weekly_total_hours.idxmin()
    min_hours = weekly_total_hours.min()

    yearly_average_hours = weekly_total_hours.groupby(
        weekly_total_hours.index.year
    ).mean()

    # 約一季的中期趨勢
    moving_average = weekly_total_hours.rolling(
        window=13,
        center=True,
    ).mean()

    return {
        "weekly_total_hours": weekly_total_hours,
        "moving_average": moving_average,
        "max_week": max_week,
        "max_hours": max_hours,
        "min_week": min_week,
        "min_hours": min_hours,
        "yearly_average_hours": yearly_average_hours,
    }


# =========================
# 5. 連續上榜區段分析
# =========================
def make_analysis_unit(row):
    # 以公開欄位建立分析鍵，並非官方唯一作品 ID；TV 不以片長切分季度。

    if row["category"].startswith("TV"):
        return f"{row['category']} | {row['show_title']} | {row['season_title']}"

    return f"{row['category']} | {row['show_title']} | runtime={row['runtime']}"


def build_consecutive_segments(df):
    """建立同一分析鍵、具有有效觀看次數且相鄰七天的上榜觀測區段。

    先排除缺 weekly_views 的列；缺值或資料起訖可能截斷區段，
    因此 streak_week 是有效觀測區段內的週次，不是完整上榜生命週期。
    """

    correlation_data = df.dropna(subset=["weekly_views"]).copy()

    if correlation_data.empty:
        return correlation_data.assign(
            analysis_unit=pd.Series(dtype="str"),
            days_since_previous=pd.Series(dtype="float64"),
            new_streak=pd.Series(dtype="bool"),
            streak_id=pd.Series(dtype="int64"),
            streak_week=pd.Series(dtype="int64"),
        )

    correlation_data["analysis_unit"] = correlation_data.apply(
        make_analysis_unit,
        axis=1,
    )

    correlation_data = correlation_data.sort_values(["analysis_unit", "week"]).copy()

    correlation_data["days_since_previous"] = (
        correlation_data.groupby("analysis_unit")["week"].diff().dt.days
    )

    # 與上一筆有效觀測不是相隔 7 天就建立新區段；
    # 可能是掉榜或觀看次數缺失，不能只由日期差判定原因。
    correlation_data["new_streak"] = correlation_data["days_since_previous"].ne(7)

    correlation_data["streak_id"] = correlation_data.groupby("analysis_unit")[
        "new_streak"
    ].cumsum()

    correlation_data["streak_week"] = (
        correlation_data.groupby(["analysis_unit", "streak_id"]).cumcount() + 1
    )

    return correlation_data


def calculate_segment_correlations(
    correlation_data,
    minimum_weeks=5,
):
    # 至少 minimum_weeks 個連續有效觀測週才計算區段內相關性；
    # 排除固定值／無效係數，不代表觀測到完整上榜生命週期。

    results = []

    grouped = correlation_data.groupby(["analysis_unit", "streak_id"])

    for (analysis_unit, streak_id), group in grouped:
        if len(group) < minimum_weeks:
            continue

        # weekly_views 完全相同時無法計算有效相關係數
        if group["weekly_views"].nunique() < 2:
            continue

        pearson = group["streak_week"].corr(
            group["weekly_views"],
            method="pearson",
        )

        spearman = group["streak_week"].corr(
            group["weekly_views"],
            method="spearman",
        )

        if pd.isna(pearson) or pd.isna(spearman):
            continue

        first_row = group.iloc[0]

        results.append(
            {
                "analysis_unit": analysis_unit,
                "streak_id": streak_id,
                "category": first_row["category"],
                "show_title": first_row["show_title"],
                "season_title": first_row["season_title"],
                "weeks": len(group),
                "pearson": pearson,
                "spearman": spearman,
            }
        )

    return pd.DataFrame(
        results,
        columns=[
            "analysis_unit", "streak_id", "category", "show_title",
            "season_title", "weeks", "pearson", "spearman",
        ],
    )


def summarize_correlations(segment_results):
    # 每個有效區段等權，並非等作品加權；同一項目可貢獻多個區段。

    if segment_results.empty:
        return {
            "segment_count": 0,
            "pearson_mean": float("nan"),
            "pearson_median": float("nan"),
            "pearson_negative_ratio": float("nan"),
            "spearman_mean": float("nan"),
            "spearman_median": float("nan"),
            "spearman_negative_ratio": float("nan"),
        }

    return {
        "segment_count": len(segment_results),
        "pearson_mean": segment_results["pearson"].mean(),
        "pearson_median": segment_results["pearson"].median(),
        "pearson_negative_ratio": (segment_results["pearson"] < 0).mean(),
        "spearman_mean": segment_results["spearman"].mean(),
        "spearman_median": segment_results["spearman"].median(),
        "spearman_negative_ratio": (segment_results["spearman"] < 0).mean(),
    }


def run_sensitivity_analysis(
    correlation_data,
    thresholds=(4, 5, 6, 8),
):
    """比較不同最低連續週數門檻的相關性結果。"""

    results = []

    for minimum_weeks in thresholds:
        segment_results = calculate_segment_correlations(
            correlation_data,
            minimum_weeks=minimum_weeks,
        )

        summary = summarize_correlations(segment_results)

        results.append(
            {
                "minimum_weeks": minimum_weeks,
                "segment_count": summary["segment_count"],
                "pearson_median": summary["pearson_median"],
                "pearson_negative_ratio": (summary["pearson_negative_ratio"]),
                "spearman_median": summary["spearman_median"],
                "spearman_negative_ratio": (summary["spearman_negative_ratio"]),
            }
        )

    return pd.DataFrame(results)


def print_correlation_results(summary, sensitivity_result, minimum_weeks=5):
    """輸出第五題摘要；沒有有效區段時不格式化缺失統計值。"""
    print(f"\n至少連續上榜 {minimum_weeks} 週的有效區段數：")
    print(summary["segment_count"])

    if summary["segment_count"] == 0:
        print("無符合條件資料")
    else:
        print("\nPearson：")
        print(f"平均數：{summary['pearson_mean']:.4f}")
        print(f"中位數：{summary['pearson_median']:.4f}")
        print(f"負相關比例：{summary['pearson_negative_ratio']:.1%}")

        print("\nSpearman：")
        print(f"平均數：{summary['spearman_mean']:.4f}")
        print(f"中位數：{summary['spearman_median']:.4f}")
        print(f"負相關比例：{summary['spearman_negative_ratio']:.1%}")

    print("\n不同最低連續週數門檻的相關性結果：")
    for _, row in sensitivity_result.iterrows():
        print(f"\n至少連續 {int(row['minimum_weeks'])} 週")
        print(f"區段數：{int(row['segment_count'])}")
        if row["segment_count"] == 0:
            print("無符合條件資料")
            continue
        print(f"Pearson 中位數：{row['pearson_median']:.4f}")
        print(f"Pearson 負相關比例：{row['pearson_negative_ratio']:.1%}")
        print(f"Spearman 中位數：{row['spearman_median']:.4f}")
        print(f"Spearman 負相關比例：{row['spearman_negative_ratio']:.1%}")


def main():
    df = load_data()
    df = add_analysis_columns(df)

    print("資料載入成功")
    print(f"資料筆數：{len(df)}")

    # 1. 電影與影集
    content_type_result = analyze_content_type(df)

    print("\n電影與影集平均每週觀看次數：")
    for content_type, value in content_type_result.items():
        print(f"{content_type}：{value:,.0f} 次")

    # 2. 英語與非英語
    language_result = analyze_language(df)

    print("\n英語與非英語內容平均每週觀看次數：")
    print(language_result)

    # 3. Top 10 停留最久作品
    top_titles = analyze_top_titles(df)

    print("\nNetflix Top 10 上榜項目最大累積週數：")
    print(top_titles.to_string(index=False))

    # 4. 時間趨勢
    trend_result = analyze_weekly_trend(df)

    print("\n每週總觀看時數最高：")
    print(f"{trend_result['max_week'].date()}：{trend_result['max_hours']:,.0f} 小時")

    print("\n每週總觀看時數最低：")
    print(f"{trend_result['min_week'].date()}：{trend_result['min_hours']:,.0f} 小時")

    print("\n各年平均每週總觀看時數：")
    for year, value in trend_result["yearly_average_hours"].items():
        print(f"{year}：{value:,.0f} 小時")

    # 5. 連續上榜相關性
    correlation_data = build_consecutive_segments(df)

    segment_results = calculate_segment_correlations(
        correlation_data,
        minimum_weeks=5,
    )

    summary = summarize_correlations(segment_results)

    sensitivity_result = run_sensitivity_analysis(correlation_data)
    print_correlation_results(summary, sensitivity_result)


if __name__ == "__main__":
    main()
