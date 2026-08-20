from scripts.analyze_data import (
    add_analysis_columns,
    analyze_content_type,
    analyze_language,
    analyze_top_titles,
    analyze_weekly_trend,
    build_consecutive_segments,
    calculate_segment_correlations,
    load_data,
    run_sensitivity_analysis,
    summarize_correlations,
)
from scripts.clean_data import (
    clean_netflix_data,
    load_raw_data,
    save_cleaned_data,
)
from scripts.fetch_data import fetch_netflix_data
from scripts.visualize import (
    configure_chinese_font,
    plot_content_type_comparison,
    plot_correlation_distribution,
    plot_language_comparison,
    plot_top_titles,
    plot_weekly_hours_trend,
)


def main():
    # =========================
    # 1. 下載原始資料
    # =========================
    print("===== 1. 下載資料 =====")

    raw_path = fetch_netflix_data()

    print("Netflix 資料下載成功")
    print(f"儲存位置：{raw_path}")

    # =========================
    # 2. 資料清洗
    # =========================
    print("\n===== 2. 資料清洗 =====")

    df = load_raw_data()

    df = clean_netflix_data(df)

    clean_path = save_cleaned_data(df)

    print("資料清洗完成")
    print(f"清洗後資料筆數：{len(df)}")
    print(f"輸出位置：{clean_path}")

    # =========================
    # 3. 載入正式分析資料
    # =========================
    print("\n===== 3. 資料分析 =====")

    df = load_data()
    df = add_analysis_columns(df)

    # -------------------------
    # 問題 1：電影與影集
    # -------------------------
    content_type_result = analyze_content_type(df)

    print("\n電影與影集平均每週觀看次數：")

    for content_type, value in content_type_result.items():
        print(f"{content_type}：{value:,.0f} 次")

    # -------------------------
    # 問題 2：英語與非英語
    # -------------------------
    language_result = analyze_language(df)

    print("\n英語與非英語內容平均每週觀看次數：")
    print(language_result)

    # -------------------------
    # 問題 3：停留最久作品
    # -------------------------
    top_titles = analyze_top_titles(df)

    print("\nNetflix Top 10 累積停留週數最多的作品：")
    print(top_titles)

    # -------------------------
    # 問題 4：時間趨勢
    # -------------------------
    trend_result = analyze_weekly_trend(df)

    print("\n每週總觀看時數最高：")
    print(f"{trend_result['max_week'].date()}：{trend_result['max_hours']:,.0f} 小時")

    print("\n每週總觀看時數最低：")
    print(f"{trend_result['min_week'].date()}：{trend_result['min_hours']:,.0f} 小時")

    print("\n各年平均每週總觀看時數：")

    for year, value in trend_result["yearly_average_hours"].items():
        print(f"{year}：{value:,.0f} 小時")

    # -------------------------
    # 問題 5：連續上榜相關性
    # -------------------------
    correlation_data = build_consecutive_segments(df)

    segment_results = calculate_segment_correlations(
        correlation_data,
        minimum_weeks=5,
    )

    summary = summarize_correlations(segment_results)

    print("\n至少連續上榜 5 週的有效區段數：")
    print(summary["segment_count"])

    print("\nPearson：")
    print(f"平均數：{summary['pearson_mean']:.4f}")
    print(f"中位數：{summary['pearson_median']:.4f}")
    print(f"負相關比例：{summary['pearson_negative_ratio']:.1%}")

    print("\nSpearman：")
    print(f"平均數：{summary['spearman_mean']:.4f}")
    print(f"中位數：{summary['spearman_median']:.4f}")
    print(f"負相關比例：{summary['spearman_negative_ratio']:.1%}")

    # 敏感度分析
    sensitivity_result = run_sensitivity_analysis(correlation_data)

    print("\n不同最低連續週數門檻的相關性結果：")

    for _, row in sensitivity_result.iterrows():
        print(f"\n至少連續 {int(row['minimum_weeks'])} 週")
        print(f"區段數：{int(row['segment_count'])}")
        print(f"Pearson 中位數：{row['pearson_median']:.4f}")
        print(f"Pearson 負相關比例：{row['pearson_negative_ratio']:.1%}")
        print(f"Spearman 中位數：{row['spearman_median']:.4f}")
        print(f"Spearman 負相關比例：{row['spearman_negative_ratio']:.1%}")

    # =========================
    # 4. 圖表輸出
    # =========================
    print("\n===== 4. 圖表輸出 =====")

    configure_chinese_font()

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
            "圖表已儲存：",
            output_path,
        )

    print("\n===== Netflix 分析流程完成 =====")


if __name__ == "__main__":
    main()
