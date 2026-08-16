from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent
input_path = project_root / "data" / "processed" / "netflix_top10_clean.csv"

df = pd.read_csv(input_path)

df["week"] = pd.to_datetime(df["week"])

print("資料筆數與欄位數：")
print(df.shape)

print("\n欄位型態：")
print(df.dtypes)

print("\n資料日期範圍：")
print("最早：", df["week"].min())
print("最新：", df["week"].max())

print("\n數值欄位基本統計：")
print(df.describe())

print("\n各內容類別資料筆數：")
print(df["category"].value_counts())

print("\n各類別平均觀看時數：")
print(df.groupby("category")["weekly_hours_viewed"].mean().sort_values(ascending=False))

print("\n各類別總觀看時數：")
print(df.groupby("category")["weekly_hours_viewed"].sum().sort_values(ascending=False))

print("\n各類別 weekly_views 有效資料筆數：")
print(df.groupby("category")["weekly_views"].count())


# ======================
# 建立電影 / 影集內容類型欄位
# ======================
df["content_type"] = df["category"].apply(
    lambda x: "Films" if x.startswith("Films") else "TV"
)

print("\n電影與影集資料筆數：")
print(df["content_type"].value_counts())

print("\n電影與影集平均觀看時數：")
print(
    df.groupby("content_type")["weekly_hours_viewed"]
    .mean()
    .sort_values(ascending=False)
)

print("\n電影與影集平均觀看次數：")
print(df.groupby("content_type")["weekly_views"].mean().sort_values(ascending=False))

print("\n電影與影集總觀看時數：")
print(
    df.groupby("content_type")["weekly_hours_viewed"].sum().sort_values(ascending=False)
)

print("\n電影與影集 weekly_views 有效資料筆數：")
print(df.groupby("content_type")["weekly_views"].count())


# ======================
# 建立英語 / 非英語內容分類欄位
# ======================
df["language_type"] = df["category"].apply(
    lambda x: "Non-English" if "Non-English" in x else "English"
)

print("\n英語與非英語內容資料筆數：")
print(df["language_type"].value_counts())

print("\n英語與非英語內容平均觀看時數：")
print(
    df.groupby("language_type")["weekly_hours_viewed"]
    .mean()
    .sort_values(ascending=False)
)

print("\n英語與非英語內容平均觀看次數：")
print(df.groupby("language_type")["weekly_views"].mean().sort_values(ascending=False))

print("\n英語與非英語內容總觀看時數：")
print(
    df.groupby("language_type")["weekly_hours_viewed"]
    .sum()
    .sort_values(ascending=False)
)

print("\n英語與非英語內容總觀看次數：")
print(df.groupby("language_type")["weekly_views"].sum().sort_values(ascending=False))

print("\n英語與非英語內容 weekly_views 有效資料筆數：")
print(df.groupby("language_type")["weekly_views"].count())


# 分析 Top 10 霸榜作品
# top10_longest = (
#     df.groupby("show_title")["week"]
#     .nunique()
#     .sort_values(ascending=False)
#     .head(10)
# )

# print("\nTop 10 停留週數最多的作品：")
# print(top10_longest)
# 不符合要分析的問題，直播也被計入

# ======================
# 分析 Top 10 霸榜作品
# ======================
top10_longest = (
    df.groupby("show_title")["cumulative_weeks_in_top_10"]
    .max()
    .sort_values(ascending=False)
    .head(10)
)

print("\nNetflix Top 10 累積停留週數最多的作品：")
print(top10_longest)


# ======================
# 時間趨勢分析
# ======================
weekly_trend = df.groupby("week")["weekly_hours_viewed"].sum().sort_index()

print("\nNetflix Top 10 每週總觀看時數：")
print(weekly_trend)

print("\n時間趨勢資料範圍：")
print("最早：", weekly_trend.index.min())
print("最晚：", weekly_trend.index.max())
print("週數：", len(weekly_trend))

highest_week = weekly_trend.idxmax()
highest_hours = weekly_trend.max()

lowest_week = weekly_trend.idxmin()
lowest_hours = weekly_trend.min()

print("\n每週總觀看時數最高：")
print("日期：", highest_week)
print("觀看時數：", highest_hours)

print("\n每週總觀看時數最低：")
print("日期：", lowest_week)
print("觀看時數：", lowest_hours)

yearly_avg_hours = weekly_trend.groupby(weekly_trend.index.year).mean()

print("\n各年平均每週觀看時數：")
print(yearly_avg_hours)

highest_week_shows = (
    df[df["week"] == highest_week]
    .sort_values("weekly_hours_viewed", ascending=False)[
        ["show_title", "category", "weekly_hours_viewed"]
    ]
    .head(10)
)

print("\n最高觀看週 Top 10 作品：")
print(highest_week_shows.to_string(index=False))

lowest_week_shows = (
    df[df["week"] == lowest_week]
    .sort_values("weekly_hours_viewed", ascending=False)[
        ["show_title", "category", "weekly_hours_viewed"]
    ]
    .head(10)
)

print("\n最低觀看週 Top 10 作品：")
print(lowest_week_shows.to_string(index=False))

weekly_moving_avg = weekly_trend.rolling(window=4).mean()

print("\n最近 10 週的 4 週移動平均：")
print(weekly_moving_avg.tail(10))

category_weekly_trend = (
    df.groupby(["week", "category"])["weekly_hours_viewed"].sum().unstack().sort_index()
)

print("\n各類別每週總觀看時數：")
print(category_weekly_trend.tail(10))

category_moving_avg = category_weekly_trend.rolling(window=4).mean()

print("\n各類別最近 10 週的 4 週移動平均：")
print(category_moving_avg.tail(10))


# ======================
# 上榜週數與觀看熱度的相關性分析
# ======================
correlation_data = df[["cumulative_weeks_in_top_10", "weekly_views"]].dropna().copy()

print("\n相關性分析有效資料筆數：")
print(len(correlation_data))

pearson_corr = correlation_data["cumulative_weeks_in_top_10"].corr(
    correlation_data["weekly_views"], method="pearson"
)

spearman_corr = correlation_data["cumulative_weeks_in_top_10"].corr(
    correlation_data["weekly_views"], method="spearman"
)

print("\n上榜累積週數與 weekly_views 的 Pearson 相關係數：")
print(pearson_corr)

print("\n上榜累積週數與 weekly_views 的 Spearman 相關係數：")
print(spearman_corr)

print("\n各類別上榜週數與 weekly_views 的相關性：")

for category, group in df.groupby("category"):
    category_data = group[["cumulative_weeks_in_top_10", "weekly_views"]].dropna()

    pearson_corr = category_data["cumulative_weeks_in_top_10"].corr(
        category_data["weekly_views"], method="pearson"
    )

    spearman_corr = category_data["cumulative_weeks_in_top_10"].corr(
        category_data["weekly_views"], method="spearman"
    )

    print(f"\n{category}")
    print(f"有效資料筆數：{len(category_data)}")
    print(f"Pearson：{pearson_corr:.4f}")
    print(f"Spearman：{spearman_corr:.4f}")


# ======================
# 上榜週數與觀看熱度的相關性分析，不可將所有作品混合
# ======================
tv_data = df[df["category"].str.startswith("TV")].copy()
# 每個 show_title 對應幾個不同 season_title
season_counts = (
    tv_data.groupby("show_title")["season_title"].nunique().sort_values(ascending=False)
)

print("\n同一 show_title 對應多個 season_title 的作品：")
print(season_counts[season_counts > 1].head(20))

# 查看其中幾個實際案例
multi_season_titles = season_counts[season_counts > 1].head(3).index

sample = tv_data[tv_data["show_title"].isin(multi_season_titles)][
    [
        "week",
        "show_title",
        "season_title",
        "cumulative_weeks_in_top_10",
        "weekly_views",
    ]
].sort_values(["show_title", "season_title", "week"])

print("\n多季作品實際資料：")
print(sample.to_string(index=False))

# 同一作品是否有重複的累積週數
duplicate_weeks = (
    df.dropna(subset=["weekly_views"])
    .groupby(
        [
            "show_title",
            "season_title",
            "cumulative_weeks_in_top_10",
        ]
    )
    .size()
)

duplicate_weeks = duplicate_weeks[duplicate_weeks > 1]

print("\n同一作品、同一累積上榜週數出現多筆的組合數：")
print(len(duplicate_weeks))

if len(duplicate_weeks) > 0:
    print("\n前 20 筆：")
    print(duplicate_weeks.head(20))

# 檢查同名作品造成的重複累積週數
duplicate_keys = duplicate_weeks.reset_index()[
    [
        "show_title",
        "season_title",
        "cumulative_weeks_in_top_10",
    ]
]

duplicate_detail = df.merge(
    duplicate_keys,
    on=[
        "show_title",
        "season_title",
        "cumulative_weeks_in_top_10",
    ],
    how="inner",
)

duplicate_detail = duplicate_detail[
    [
        "week",
        "category",
        "weekly_rank",
        "show_title",
        "season_title",
        "cumulative_weeks_in_top_10",
        "weekly_views",
        "runtime",
    ]
].sort_values(
    [
        "show_title",
        "season_title",
        "week",
    ]
)

print("\n重複累積週數的完整資料：")
print(duplicate_detail.to_string(index=False))

# 建立作品分析單位
correlation_data = df.dropna(subset=["weekly_views"]).copy()


def make_analysis_unit(row):
    if row["category"].startswith("TV"):
        return f"{row['category']} | {row['show_title']} | {row['season_title']}"

    return f"{row['category']} | {row['show_title']} | runtime={row['runtime']}"


correlation_data["analysis_unit"] = correlation_data.apply(make_analysis_unit, axis=1)

duplicate_check = correlation_data.groupby(
    [
        "analysis_unit",
        "cumulative_weeks_in_top_10",
    ]
).size()

duplicate_check = duplicate_check[duplicate_check > 1]

print("\n建立 analysis_unit 後，同一作品同一累積週數仍重複的組合數：")
print(len(duplicate_check))

if len(duplicate_check) > 0:
    print(duplicate_check.head(20))

unit_counts = (
    correlation_data.groupby("analysis_unit").size().sort_values(ascending=False)
)

print("\n每個分析單位的有效週數統計：")
print(unit_counts.describe())

print("\n不同最低週數門檻可分析的作品數：")

for minimum_weeks in [2, 3, 4, 5, 6, 8, 10]:
    count = (unit_counts >= minimum_weeks).sum()

    print(f"至少 {minimum_weeks} 筆有效 weekly_views 觀測：{count} 個作品")

print("\n有效週數最多的前 20 個分析單位：")
print(unit_counts.head(20))

# 測試舊資料有weekly_views的資料筆數
squid_game_s1 = df[
    (df["show_title"] == "Squid Game") & (df["season_title"] == "Squid Game: Season 1")
][
    [
        "week",
        "category",
        "weekly_rank",
        "show_title",
        "season_title",
        "cumulative_weeks_in_top_10",
        "weekly_views",
    ]
].sort_values("week")

print("\nSquid Game: Season 1 全部紀錄：")
print(squid_game_s1.to_string(index=False))

print("\n總上榜資料筆數：")
print(len(squid_game_s1))

print("\n有 weekly_views 的資料筆數：")
print(squid_game_s1["weekly_views"].notna().sum())

print("\n最大 cumulative_weeks_in_top_10：")
print(squid_game_s1["cumulative_weeks_in_top_10"].max())


# ======================
# 上榜週數與觀看熱度的相關性分析，不可將所有作品混合，且上榜週需要有連續性
# ======================
correlation_data = correlation_data.sort_values(["analysis_unit", "week"]).copy()

correlation_data["days_since_previous"] = (
    correlation_data.groupby("analysis_unit")["week"].diff().dt.days
)

# 不是相隔 7 天，就視為新的連續上榜區段
correlation_data["new_streak"] = correlation_data["days_since_previous"].ne(7)

# 為每個作品建立不同 streak
correlation_data["streak_id"] = correlation_data.groupby("analysis_unit")[
    "new_streak"
].cumsum()

# 計算每一個 streak 中的第幾週
correlation_data["streak_week"] = (
    correlation_data.groupby(["analysis_unit", "streak_id"]).cumcount() + 1
)

squid_streak = correlation_data[
    (correlation_data["show_title"] == "Squid Game")
    & (correlation_data["season_title"] == "Squid Game: Season 1")
][
    [
        "week",
        "weekly_views",
        "cumulative_weeks_in_top_10",
        "streak_id",
        "streak_week",
    ]
]

print("\nSquid Game Season 1 連續上榜區段：")
print(squid_streak.to_string(index=False))

# 計算每個連續上榜區段有幾筆有效 weekly_views
streak_counts = (
    correlation_data.groupby(["analysis_unit", "streak_id"])
    .size()
    .sort_values(ascending=False)
)

print("\n連續上榜區段長度統計：")
print(streak_counts.describe())

print("\n不同最低連續週數可分析的區段數：")

for minimum_weeks in [2, 3, 4, 5, 6, 8, 10]:
    count = (streak_counts >= minimum_weeks).sum()

    print(f"至少連續 {minimum_weeks} 週：{count} 個區段")

print("\n最長的前 20 個連續上榜區段：")
print(streak_counts.head(20))

# 至少連續 5 週才納入相關性分析
minimum_weeks = 5

streak_results = []

for (analysis_unit, streak_id), group in correlation_data.groupby(
    ["analysis_unit", "streak_id"]
):
    if len(group) < minimum_weeks:
        continue

    # 如果整個區段 weekly_views 都相同，
    # 沒有變異，無法計算有效相關係數
    if group["weekly_views"].nunique() < 2:
        continue

    pearson_corr = group["streak_week"].corr(group["weekly_views"], method="pearson")

    spearman_corr = group["streak_week"].corr(group["weekly_views"], method="spearman")

    streak_results.append(
        {
            "analysis_unit": analysis_unit,
            "streak_id": streak_id,
            "weeks": len(group),
            "pearson": pearson_corr,
            "spearman": spearman_corr,
        }
    )

streak_corr_df = pd.DataFrame(streak_results)

print("\n實際完成相關性分析的連續上榜區段數：")
print(len(streak_corr_df))

print("\nPearson / Spearman 統計摘要：")
print(streak_corr_df[["pearson", "spearman"]].describe())

pearson_negative = (streak_corr_df["pearson"] < 0).sum()
pearson_positive = (streak_corr_df["pearson"] > 0).sum()
pearson_zero = (streak_corr_df["pearson"] == 0).sum()

spearman_negative = (streak_corr_df["spearman"] < 0).sum()
spearman_positive = (streak_corr_df["spearman"] > 0).sum()
spearman_zero = (streak_corr_df["spearman"] == 0).sum()

total = len(streak_corr_df)

print("\nPearson 方向分布：")
print(f"負相關：{pearson_negative} ({pearson_negative / total:.1%})")
print(f"正相關：{pearson_positive} ({pearson_positive / total:.1%})")
print(f"零相關：{pearson_zero} ({pearson_zero / total:.1%})")

print("\nSpearman 方向分布：")
print(f"負相關：{spearman_negative} ({spearman_negative / total:.1%})")
print(f"正相關：{spearman_positive} ({spearman_positive / total:.1%})")
print(f"零相關：{spearman_zero} ({spearman_zero / total:.1%})")

print("\n相關係數中位數：")
print(f"Pearson：{streak_corr_df['pearson'].median():.4f}")
print(f"Spearman：{streak_corr_df['spearman'].median():.4f}")

# 敏感度分析
print("\n不同最低連續週數門檻的相關性結果：")

for minimum_weeks in [4, 5, 6, 8]:
    threshold_results = []

    for (analysis_unit, streak_id), group in correlation_data.groupby(
        ["analysis_unit", "streak_id"]
    ):
        if len(group) < minimum_weeks:
            continue

        if group["weekly_views"].nunique() < 2:
            continue

        pearson_corr = group["streak_week"].corr(
            group["weekly_views"], method="pearson"
        )

        spearman_corr = group["streak_week"].corr(
            group["weekly_views"], method="spearman"
        )

        threshold_results.append(
            {
                "pearson": pearson_corr,
                "spearman": spearman_corr,
            }
        )

    threshold_df = pd.DataFrame(threshold_results)

    pearson_negative_rate = threshold_df["pearson"].lt(0).mean()

    spearman_negative_rate = threshold_df["spearman"].lt(0).mean()

    print(f"\n至少連續 {minimum_weeks} 週")
    print(f"區段數：{len(threshold_df)}")
    print(f"Pearson 中位數：{threshold_df['pearson'].median():.4f}")
    print(f"Pearson 負相關比例：{pearson_negative_rate:.1%}")
    print(f"Spearman 中位數：{threshold_df['spearman'].median():.4f}")
    print(f"Spearman 負相關比例：{spearman_negative_rate:.1%}")
