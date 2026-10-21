"""只驗證人造資料的離線串接，不代表正式 Netflix CSV 或完整主程式已驗收。"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

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
from scripts.clean_data import clean_netflix_data, save_cleaned_data
from scripts.visualize import (
    configure_chinese_font,
    plot_content_type_comparison,
    plot_correlation_distribution,
    plot_language_comparison,
    plot_top_titles,
    plot_weekly_hours_trend,
)
from tests.test_analysis import test_consecutive_segments, test_data_quality


def make_pipeline_data():
    rows = []
    for category in [
        "Films (English)", "Films (Non-English)",
        "TV (English)", "TV (Non-English)",
    ]:
        runtime = 2.0 if category.startswith("Films") else 4.0
        for i, week in enumerate(pd.date_range("2026-01-04", periods=14, freq="7D")):
            views = 1400 - 100 * i
            rows.append({
                "week": week, "category": category, "weekly_rank": 1,
                "show_title": f"離線測試 {category}",
                "season_title": None if category.startswith("Films") else "Season 1",
                "weekly_hours_viewed": int(views * runtime),
                "runtime": runtime if i else 0.0,
                "weekly_views": views if i else None,
                "cumulative_weeks_in_top_10": i + 1,
            })
    # 一筆完全重複資料，讓清洗及讀寫的銜接也經過實際資料變化。
    rows.append(rows[0].copy())
    return pd.DataFrame(rows)


class OfflinePipelineTests(unittest.TestCase):
    def test_synthetic_clean_csv_analysis_and_five_charts(self):
        """人造四類、14 週；所有檔案只存在於自動清除的暫存資料夾。"""
        configure_chinese_font()
        with TemporaryDirectory() as folder:
            try:
                cleaned = clean_netflix_data(make_pipeline_data())
                self.assertEqual(len(cleaned), 56)
                self.assertEqual(int(cleaned.runtime.isna().sum()), 4)
                self.assertEqual(int(cleaned.weekly_views.isna().sum()), 4)

                csv_path = Path(folder) / "processed" / "synthetic_clean.csv"
                self.assertEqual(save_cleaned_data(cleaned, output_path=csv_path), csv_path)
                self.assertEqual(csv_path.read_bytes()[:3], b"\xef\xbb\xbf")
                loaded = load_data(csv_path)
                pd.testing.assert_frame_equal(loaded, cleaned, check_dtype=False)
                self.assertTrue(pd.api.types.is_datetime64_any_dtype(loaded.week))
                for column in ["weekly_rank", "weekly_hours_viewed", "runtime",
                               "weekly_views", "cumulative_weeks_in_top_10"]:
                    self.assertTrue(pd.api.types.is_numeric_dtype(loaded[column]))

                # 重用原有完整檢查，明確傳入人造 CSV，不讀正式預設路徑。
                test_data_quality(input_path=csv_path)
                test_consecutive_segments(input_path=csv_path)

                data = add_analysis_columns(loaded)
                self.assertEqual(set(data.content_type), {"Films", "TV"})
                self.assertEqual(set(data.language_type), {"English", "Non-English"})

                content = analyze_content_type(data)
                self.assertEqual(content.to_dict(), {"Films": 700.0, "TV": 700.0})
                language = analyze_language(data)
                self.assertEqual(language.shape, (2, 2))
                self.assertTrue(language.eq(700.0).all().all())

                top = analyze_top_titles(data)
                self.assertEqual(top.columns.tolist(), [
                    "category", "show_title", "season_title", "cumulative_weeks_in_top_10"
                ])
                self.assertEqual(len(top), 4)
                self.assertEqual(top.cumulative_weeks_in_top_10.tolist(), [14] * 4)

                trend = analyze_weekly_trend(data)
                self.assertEqual(len(trend["weekly_total_hours"]), 14)
                self.assertEqual(trend["max_hours"], 16800)
                self.assertEqual(trend["min_hours"], 1200)
                self.assertTrue(trend["moving_average"].notna().any())

                segments = build_consecutive_segments(data)
                results = calculate_segment_correlations(segments)
                self.assertEqual(len(results), 4)
                self.assertEqual(results.weeks.tolist(), [13] * 4)
                summary = summarize_correlations(results)
                self.assertEqual(summary["segment_count"], 4)
                self.assertAlmostEqual(summary["pearson_median"], -1.0)
                self.assertAlmostEqual(summary["spearman_median"], -1.0)
                sensitivity = run_sensitivity_analysis(segments)
                self.assertEqual(sensitivity.minimum_weeks.tolist(), [4, 5, 6, 8])
                self.assertEqual(sensitivity.segment_count.tolist(), [4] * 4)

                charts_dir = Path(folder) / "charts"
                chart_functions = [
                    plot_content_type_comparison, plot_language_comparison, plot_top_titles,
                    plot_weekly_hours_trend, plot_correlation_distribution,
                ]
                expected_names = [
                    "01_films_vs_tv_average_views.png",
                    "02_english_vs_non_english_average_views.png",
                    "03_top10_longest_stay_titles.png",
                    "04_weekly_total_hours_trend.png",
                    "05_continuous_run_correlation_distribution.png",
                ]
                for function, name in zip(chart_functions, expected_names):
                    with self.subTest(chart=name):
                        result = function(data, charts_dir=charts_dir)
                        self.assertEqual(result, charts_dir / name)
                        with Image.open(result) as image:
                            self.assertEqual(image.format, "PNG")
                            image.verify()
                self.assertEqual(sorted(p.name for p in charts_dir.iterdir()), expected_names)
            finally:
                plt.close("all")
        self.assertFalse(Path(folder).exists())


if __name__ == "__main__":
    unittest.main()
