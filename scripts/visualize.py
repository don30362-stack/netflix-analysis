from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from matplotlib import font_manager

project_root = Path(__file__).resolve().parent.parent
input_path = project_root / "data" / "processed" / "netflix_top10_clean.csv"

charts_dir = project_root / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_path)

df["week"] = pd.to_datetime(df["week"])


# 設定中文字型
available_fonts = {font.name for font in font_manager.fontManager.ttflist}

font_candidates = [
    "Microsoft JhengHei",
    "PingFang HK",
    "Heiti TC",
    "Noto Sans CJK TC",
    "Microsoft YaHei",
]

for font_name in font_candidates:
    if font_name in available_fonts:
        plt.rcParams["font.family"] = font_name
        print("使用中文字型：", font_name)
        break
else:
    print("警告：找不到預設中文字型，圖表可能出現中文亂碼")

plt.rcParams["axes.unicode_minus"] = False

print("資料載入成功")
print("資料筆數：", len(df))
print("圖表輸出位置：", charts_dir)


# =========================
# 1. 電影與影集熱門程度比較
# =========================

views_df = df.dropna(subset=["weekly_views"]).copy()

views_df["content_type"] = views_df["category"].apply(
    lambda x: "電影" if x.startswith("Films") else "影集"
)

content_type_views = (
    views_df.groupby("content_type")["weekly_views"].mean().reindex(["電影", "影集"])
)

print("\nweekly_views 有效資料期間：")
print("最早：", views_df["week"].min().date())
print("最晚：", views_df["week"].max().date())

print("\n電影與影集平均每週觀看次數：")
for content_type, value in content_type_views.items():
    print(f"{content_type}：{value:,.0f} 次")

# 將數字轉換成「百萬次」，避免圖表出現 1e7 科學記號
content_type_views_million = content_type_views / 1_000_000


fig, ax = plt.subplots(figsize=(8, 5.5))

bars = ax.bar(
    content_type_views_million.index,
    content_type_views_million.values,
    width=0.55,
    color=["#4C78A8", "#F58518"],
)

ax.set_title(
    "Netflix 電影與影集平均每週觀看次數比較",
    fontsize=16,
    fontweight="bold",
    pad=15,
)

ax.set_xlabel("內容類型", fontsize=12)
ax.set_ylabel("平均每週觀看次數（百萬次）", fontsize=12)

# 在柱狀圖上直接顯示數值
for bar, value in zip(bars, content_type_views_million.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"{value:.1f}",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

# 留出柱頂數字的顯示空間
ax.set_ylim(
    0,
    content_type_views_million.max() * 1.18,
)

# 提高可讀性
ax.yaxis.grid(
    True,
    linestyle="--",
    alpha=0.3,
)

ax.set_axisbelow(True)

# 移除不必要的外框
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

output_path = charts_dir / "01_films_vs_tv_average_views.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("\n圖表已儲存：", output_path)


# =========================
# 2. 英語與非英語內容熱門程度比較
# =========================

views_df["content_type_zh"] = views_df["category"].apply(
    lambda x: "電影" if x.startswith("Films") else "影集"
)

views_df["language_type_zh"] = views_df["category"].apply(
    lambda x: "非英語" if "Non-English" in x else "英語"
)

language_views = (
    views_df.groupby(["content_type_zh", "language_type_zh"])["weekly_views"]
    .mean()
    .unstack()
    .reindex(index=["電影", "影集"], columns=["英語", "非英語"])
)

print("\n英語與非英語內容平均每週觀看次數：")
print(language_views)

language_views_million = language_views / 1_000_000

x = np.arange(len(language_views_million.index))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5.8))

bars_english = ax.bar(
    x - width / 2,
    language_views_million["英語"],
    width,
    label="英語",
    color="#4C78A8",
)

bars_non_english = ax.bar(
    x + width / 2,
    language_views_million["非英語"],
    width,
    label="非英語",
    color="#F58518",
)

ax.set_title(
    "Netflix 英語與非英語內容平均每週觀看次數比較",
    fontsize=16,
    fontweight="bold",
    pad=15,
)

ax.set_xlabel("內容類型", fontsize=12)
ax.set_ylabel("平均每週觀看次數（百萬次）", fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(language_views_million.index, fontsize=11)

ax.legend(title="語言類型", frameon=False)

# 顯示每根柱子的數值
for bars in [bars_english, bars_non_english]:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.1f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

ax.set_ylim(0, language_views_million.max().max() * 1.18)

ax.yaxis.grid(True, linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

output_path = charts_dir / "02_english_vs_non_english_average_views.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("\n圖表已儲存：", output_path)


# =========================
# 3. 累積停留週數最久作品排行
# =========================

top_titles = (
    df.groupby("show_title")["cumulative_weeks_in_top_10"]
    .max()
    .sort_values(ascending=False)
    .head(10)
    .sort_values(ascending=True)
)

print("\n累積停留週數最久的前 10 名作品：")
print(top_titles)

fig, ax = plt.subplots(figsize=(10, 6.5))

bars = ax.barh(
    top_titles.index,
    top_titles.values,
    color="#4C78A8",
)

ax.set_title(
    "Netflix Top 10 累積停留週數最久作品",
    fontsize=16,
    fontweight="bold",
    pad=15,
)

ax.set_xlabel("累積停留週數", fontsize=12)
ax.set_ylabel("作品名稱", fontsize=12)

# 在每個長條右側標示數值
for bar, value in zip(bars, top_titles.values):
    ax.text(
        value + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"{value}",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

ax.xaxis.grid(True, linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

output_path = charts_dir / "03_top10_longest_stay_titles.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("\n圖表已儲存：", output_path)


# =========================
# 4. Netflix Top 10 整體每週觀看時數趨勢
# =========================

weekly_total_hours = df.groupby("week")["weekly_hours_viewed"].sum().sort_index()

# 13 週移動平均，約代表一季的中期趨勢
weekly_total_hours_ma13 = weekly_total_hours.rolling(window=13, center=True).mean()

print("\nNetflix Top 10 每週總觀看時數：")
print(weekly_total_hours.head())

# 找出最高與最低週
max_week = weekly_total_hours.idxmax()
max_hours = weekly_total_hours.max()

min_week = weekly_total_hours.idxmin()
min_hours = weekly_total_hours.min()

print("\n每週總觀看時數最高：")
print(f"{max_week.date()}：{max_hours:,.0f} 小時")

print("\n每週總觀看時數最低：")
print(f"{min_week.date()}：{min_hours:,.0f} 小時")


# 計算各年平均每週觀看時數
yearly_average_hours = weekly_total_hours.groupby(weekly_total_hours.index.year).mean()

print("\n各年平均每週總觀看時數：")
for year, value in yearly_average_hours.items():
    print(f"{year}：{value:,.0f} 小時")


# 將單位轉換為「百萬小時」
weekly_total_hours_million = weekly_total_hours / 1_000_000
weekly_total_hours_ma13_million = weekly_total_hours_ma13 / 1_000_000


fig, ax = plt.subplots(figsize=(12, 6.5))

# 原始每週資料
ax.plot(
    weekly_total_hours_million.index,
    weekly_total_hours_million.values,
    linewidth=1.2,
    alpha=0.45,
    color="#9E9E9E",
    label="每週總觀看時數",
)

# 13 週移動平均
ax.plot(
    weekly_total_hours_ma13_million.index,
    weekly_total_hours_ma13_million.values,
    linewidth=2.8,
    color="#C62828",
    label="13 週移動平均趨勢",
)


ax.set_title(
    "Netflix Top 10 整體每週觀看時數趨勢",
    fontsize=16,
    fontweight="bold",
    pad=15,
)

ax.set_xlabel("日期", fontsize=12)
ax.set_ylabel("每週總觀看時數（百萬小時）", fontsize=12)


# 每年顯示一個日期刻度
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


ax.legend(
    frameon=False,
    fontsize=11,
)


ax.yaxis.grid(
    True,
    linestyle="--",
    alpha=0.3,
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()


output_path = charts_dir / "04_weekly_total_hours_trend.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("\n圖表已儲存：", output_path)


# =========================
# 5. 連續上榜期間與觀看熱度相關性
# =========================

correlation_df = df.dropna(subset=["weekly_views"]).copy()

correlation_df = correlation_df.sort_values(["category", "show_title", "week"])

segment_results = []

for (category, show_title, season_title), group in correlation_df.groupby(
    ["category", "show_title", "season_title"]
):
    group = group.sort_values("week").copy()

    # 若與上一筆資料不是相隔 7 天，
    # 代表中途曾掉出 Top 10，建立新的連續上榜區段
    group["new_segment"] = group["week"].diff().dt.days.ne(7)

    group["segment_id"] = group["new_segment"].cumsum()

    for segment_id, segment in group.groupby("segment_id"):

        # 主分析只納入至少連續上榜 5 週的區段
        if len(segment) < 5:
            continue

        segment = segment.sort_values("week").copy()

        # 建立「本次連續上榜的第幾週」
        segment["consecutive_week"] = range(1, len(segment) + 1)

        pearson = segment["consecutive_week"].corr(
            segment["weekly_views"],
            method="pearson",
        )

        spearman = segment["consecutive_week"].corr(
            segment["weekly_views"], method="spearman"
        )

        segment_results.append(
            {
                "category": category,
                "show_title": show_title,
                "season_title": season_title,
                "segment_id": segment_id,
                "weeks": len(segment),
                "pearson": pearson,
                "spearman": spearman,
            }
        )


segment_results_df = pd.DataFrame(segment_results)

print("\n至少連續上榜 5 週的有效區段數：")
print(len(segment_results_df))

print("\nPearson：")
print(f"中位數：{segment_results_df['pearson'].median():.4f}")
print("負相關比例：" f"{(segment_results_df['pearson'] < 0).mean() * 100:.1f}%")

print("\nSpearman：")
print(f"中位數：{segment_results_df['spearman'].median():.4f}")
print("負相關比例：" f"{(segment_results_df['spearman'] < 0).mean() * 100:.1f}%")


pearson_median = segment_results_df["pearson"].median()
spearman_median = segment_results_df["spearman"].median()

pearson_negative_ratio = (
    (segment_results_df["pearson"] < 0).mean() * 100
)

spearman_negative_ratio = (
    (segment_results_df["spearman"] < 0).mean() * 100
)


fig, ax = plt.subplots(figsize=(10, 6))

bins = np.linspace(-1, 1, 21)

ax.hist(
    segment_results_df["pearson"],
    bins=bins,
    alpha=0.55,
    label="Pearson",
    color="#4C78A8",
    edgecolor="white",
)

ax.hist(
    segment_results_df["spearman"],
    bins=bins,
    histtype="step",
    linewidth=2.2,
    label="Spearman",
    color="#F58518",
)


# 相關係數 = 0 的基準線
ax.axvline(
    0,
    color="#555555",
    linestyle="--",
    linewidth=1.5,
    label="零相關",
)


# 中位數位置
# ax.axvline(
#     pearson_median,
#     color="#4C78A8",
#     linestyle=":",
#     linewidth=2,
#     label="Pearson 中位數",
# )

# ax.axvline(
#     spearman_median,
#     color="#F58518",
#     linestyle=":",
#     linewidth=2,
#     label="Spearman 中位數",
# )


ax.set_title(
    "至少連續上榜 5 週區段的觀看熱度相關係數分布",
    fontsize=16,
    fontweight="bold",
    pad=15,
)

ax.set_xlabel("連續上榜週次與當週觀看次數的相關係數", fontsize=12)
ax.set_ylabel("區段數", fontsize=12)

ax.set_xlim(-1.05, 1.05)

ax.yaxis.grid(
    True,
    linestyle="--",
    alpha=0.3,
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)


# 直接在圖上顯示主要統計結果
summary_text = (
    f"有效區段：{len(segment_results_df)}\n"
    f"Pearson 中位數：{pearson_median:.4f}\n"
    f"Pearson 負相關：{pearson_negative_ratio:.1f}%\n"
    f"Spearman 中位數：{spearman_median:.4f}\n"
    f"Spearman 負相關：{spearman_negative_ratio:.1f}%"
)

ax.text(
    0.97,
    0.95,
    summary_text,
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=10.5,
    bbox={
        "boxstyle": "round,pad=0.5",
        "facecolor": "white",
        "edgecolor": "#CCCCCC",
        "alpha": 0.9,
    },
)

ax.legend(
    frameon=False,
    loc="lower right",
)

plt.tight_layout()


output_path = charts_dir / "05_continuous_run_correlation_distribution.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("\n圖表已儲存：", output_path)
