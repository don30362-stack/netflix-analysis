from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
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
