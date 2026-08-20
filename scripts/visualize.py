from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from scripts.analyze_data import (
    add_analysis_columns,
    analyze_content_type,
    analyze_language,
    analyze_top_titles,
    analyze_weekly_trend,
    build_consecutive_segments,
    calculate_segment_correlations,
    load_data,
    summarize_correlations,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHARTS_DIR = PROJECT_ROOT / "charts"


def configure_chinese_font():
    # 設定 Matplotlib 可用的中文字型。

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


# =========================
# 1. 電影與影集熱門程度比較
# =========================
def plot_content_type_comparison(
    df,
    charts_dir=DEFAULT_CHARTS_DIR,
):
    # 繪製電影與影集平均每週觀看次數比較圖。

    content_type_views = analyze_content_type(df)

    content_type_views = content_type_views.rename(
        {
            "Films": "電影",
            "TV": "影集",
        }
    )

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

    ax.set_ylabel(
        "平均每週觀看次數（百萬次）",
        fontsize=12,
    )

    for bar in bars:
        value = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_ylim(
        0,
        content_type_views_million.max() * 1.18,
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

    output_path = charts_dir / "01_films_vs_tv_average_views.png"

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# =========================
# 2. 英語與非英語內容比較
# =========================
def plot_language_comparison(
    df,
    charts_dir=DEFAULT_CHARTS_DIR,
):
    # 繪製英語與非英語內容平均觀看次數比較圖。

    language_views = analyze_language(df)

    language_views = language_views.rename(
        index={
            "Films": "電影",
            "TV": "影集",
        },
        columns={
            "English": "英語",
            "Non-English": "非英語",
        },
    )

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

    ax.set_ylabel(
        "平均每週觀看次數（百萬次）",
        fontsize=12,
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        language_views_million.index,
        fontsize=11,
    )

    ax.legend(
        title="語言類型",
        frameon=False,
    )

    for bars in [
        bars_english,
        bars_non_english,
    ]:
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

    ax.set_ylim(
        0,
        language_views_million.max().max() * 1.18,
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

    output_path = charts_dir / "02_english_vs_non_english_average_views.png"

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# =========================
# 3. Top 10 停留最久作品
# =========================
def plot_top_titles(
    df,
    charts_dir=DEFAULT_CHARTS_DIR,
):
    # 繪製 Top 10 累積停留週數最久作品排行。

    top_titles = analyze_top_titles(
        df,
        top_n=10,
    ).sort_values()

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

    ax.set_xlabel(
        "累積停留週數",
        fontsize=12,
    )

    ax.set_ylabel(
        "作品名稱",
        fontsize=12,
    )

    for bar in bars:
        value = bar.get_width()

        ax.text(
            value + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.0f}",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    ax.xaxis.grid(
        True,
        linestyle="--",
        alpha=0.3,
    )

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

    return output_path


# =========================
# 4. 每週觀看時數趨勢
# =========================
def plot_weekly_hours_trend(
    df,
    charts_dir=DEFAULT_CHARTS_DIR,
):
    # 繪製 Netflix Top 10 每週觀看時數趨勢圖。

    trend_result = analyze_weekly_trend(df)

    weekly_total_hours = trend_result["weekly_total_hours"] / 1_000_000

    moving_average = trend_result["moving_average"] / 1_000_000

    fig, ax = plt.subplots(figsize=(12, 6.5))

    ax.plot(
        weekly_total_hours.index,
        weekly_total_hours.values,
        linewidth=1.2,
        alpha=0.45,
        color="#9E9E9E",
        label="每週總觀看時數",
    )

    ax.plot(
        moving_average.index,
        moving_average.values,
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

    ax.set_xlabel(
        "日期",
        fontsize=12,
    )

    ax.set_ylabel(
        "每週總觀看時數（百萬小時）",
        fontsize=12,
    )

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

    return output_path


# =========================
# 5. 連續上榜相關係數分布
# =========================
def plot_correlation_distribution(
    df,
    charts_dir=DEFAULT_CHARTS_DIR,
    minimum_weeks=5,
):
    """繪製連續上榜區段 Pearson / Spearman 分布。"""

    correlation_data = build_consecutive_segments(df)

    segment_results = calculate_segment_correlations(
        correlation_data,
        minimum_weeks=minimum_weeks,
    )

    summary = summarize_correlations(segment_results)

    fig, ax = plt.subplots(figsize=(10, 6))

    bins = np.linspace(
        -1,
        1,
        21,
    )

    ax.hist(
        segment_results["pearson"],
        bins=bins,
        alpha=0.55,
        label="Pearson",
        color="#4C78A8",
        edgecolor="white",
    )

    ax.hist(
        segment_results["spearman"],
        bins=bins,
        histtype="step",
        linewidth=2.2,
        label="Spearman",
        color="#F58518",
    )

    ax.axvline(
        0,
        color="#555555",
        linestyle="--",
        linewidth=1.5,
        label="零相關",
    )

    ax.set_title(
        f"至少連續上榜 {minimum_weeks} 週區段的觀看熱度相關係數分布",
        fontsize=16,
        fontweight="bold",
        pad=15,
    )

    ax.set_xlabel(
        "連續上榜週次與當週觀看次數的相關係數",
        fontsize=12,
    )

    ax.set_ylabel(
        "區段數",
        fontsize=12,
    )

    ax.set_xlim(
        -1.05,
        1.05,
    )

    ax.yaxis.grid(
        True,
        linestyle="--",
        alpha=0.3,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    summary_text = (
        f"有效區段："
        f"{summary['segment_count']}\n"
        f"Pearson 中位數："
        f"{summary['pearson_median']:.4f}\n"
        f"Pearson 負相關："
        f"{summary['pearson_negative_ratio']:.1%}\n"
        f"Spearman 中位數："
        f"{summary['spearman_median']:.4f}\n"
        f"Spearman 負相關："
        f"{summary['spearman_negative_ratio']:.1%}"
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

    return output_path


def main():
    DEFAULT_CHARTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    configure_chinese_font()

    df = load_data()
    df = add_analysis_columns(df)

    print("資料載入成功")
    print("資料筆數：", len(df))
    print(
        "圖表輸出位置：",
        DEFAULT_CHARTS_DIR,
    )

    chart_functions = [
        plot_content_type_comparison,
        plot_language_comparison,
        plot_top_titles,
        plot_weekly_hours_trend,
        plot_correlation_distribution,
    ]

    for chart_function in chart_functions:
        output_path = chart_function(df)
        print(
            "\n圖表已儲存：",
            output_path,
        )


if __name__ == "__main__":
    main()
