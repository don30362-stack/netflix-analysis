from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from scripts.analyze_data import (
    add_analysis_columns,
    build_consecutive_segments,
    calculate_segment_correlations,
    print_correlation_results,
    run_sensitivity_analysis,
    summarize_correlations,
)
from scripts.visualize import (
    configure_chinese_font,
    plot_content_type_comparison,
    plot_correlation_distribution,
    plot_language_comparison,
    plot_top_titles,
    plot_weekly_hours_trend,
)


RESULT_COLUMNS = [
    "analysis_unit", "streak_id", "category", "show_title",
    "season_title", "weeks", "pearson", "spearman",
]


def make_data(views=(600, 500, 400, 300, 200, 100)):
    rows = []
    for category in [
        "Films (English)", "Films (Non-English)",
        "TV (English)", "TV (Non-English)",
    ]:
        for i, (week, value) in enumerate(zip(
            pd.date_range("2026-01-04", periods=len(views), freq="7D"), views
        ), start=1):
            rows.append({
                "week": week, "category": category, "weekly_rank": 1,
                "show_title": f"Offline {category}", "season_title": "Season 1",
                "weekly_hours_viewed": 1000 * i, "runtime": 2.0,
                "weekly_views": value, "cumulative_weeks_in_top_10": i,
            })
    return pd.DataFrame(rows)


class CorrelationReliabilityTests(unittest.TestCase):
    def assert_empty_result(self, result):
        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), RESULT_COLUMNS)
        summary = summarize_correlations(result)
        self.assertEqual(summary["segment_count"], 0)
        self.assertTrue(all(pd.isna(v) for k, v in summary.items() if k != "segment_count"))

    def test_empty_input(self):
        segments = build_consecutive_segments(make_data().iloc[:0])
        self.assert_empty_result(calculate_segment_correlations(segments))

    def test_all_views_missing(self):
        segments = build_consecutive_segments(make_data((None,) * 6))
        self.assert_empty_result(calculate_segment_correlations(segments))

    def test_all_segments_too_short(self):
        segments = build_consecutive_segments(make_data((300, 200, 100)))
        self.assert_empty_result(calculate_segment_correlations(segments, minimum_weeks=5))

    def test_constant_views(self):
        segments = build_consecutive_segments(make_data((100,) * 6))
        self.assert_empty_result(calculate_segment_correlations(segments))

    def test_partial_sensitivity_results(self):
        segments = build_consecutive_segments(make_data())
        result = run_sensitivity_analysis(segments)
        self.assertEqual(result["minimum_weeks"].tolist(), [4, 5, 6, 8])
        self.assertEqual(result["segment_count"].tolist(), [4, 4, 4, 0])
        metrics = result.columns.difference(["minimum_weeks", "segment_count"])
        self.assertTrue(result.loc[3, metrics].isna().all())
        for column in metrics:
            expected = 1.0 if column.endswith("negative_ratio") else -1.0
            for value in result.loc[:2, column]:
                self.assertAlmostEqual(value, expected)

    def test_all_sensitivity_thresholds_empty(self):
        for data in [make_data().iloc[:0], make_data((100,) * 6)]:
            with self.subTest(rows=len(data)):
                result = run_sensitivity_analysis(build_consecutive_segments(data))
                self.assertEqual(result["segment_count"].tolist(), [0, 0, 0, 0])
                self.assertTrue(result.drop(columns=["minimum_weeks", "segment_count"]).isna().all().all())

    def test_valid_nonlinear_correlations(self):
        segments = build_consecutive_segments(make_data((1, 4, 9, 16, 25)))
        result = calculate_segment_correlations(segments)
        self.assertEqual(result.columns.tolist(), RESULT_COLUMNS)
        self.assertEqual(len(result), 4)
        for value in result["pearson"]:
            self.assertAlmostEqual(value, 0.981104910251593)
        for value in result["spearman"]:
            self.assertAlmostEqual(value, 1.0)
        summary = summarize_correlations(result)
        self.assertEqual(summary["segment_count"], 4)
        self.assertAlmostEqual(summary["pearson_mean"], 0.981104910251593)
        self.assertAlmostEqual(summary["spearman_median"], 1.0)
        self.assertEqual(summary["pearson_negative_ratio"], 0.0)
        self.assertEqual(summary["spearman_negative_ratio"], 0.0)

    def test_console_output_with_empty_and_valid_thresholds(self):
        segments = build_consecutive_segments(make_data())
        for minimum_weeks in (5, 8):
            with self.subTest(minimum_weeks=minimum_weeks):
                summary = summarize_correlations(
                    calculate_segment_correlations(segments, minimum_weeks=minimum_weeks)
                )
                output = StringIO()
                with redirect_stdout(output):
                    print_correlation_results(summary, run_sensitivity_analysis(segments), minimum_weeks)
                text = output.getvalue()
                self.assertIn("無符合條件資料", text)
                self.assertIn("100.0%", text)
                self.assertNotIn("nan", text.lower())


class ChartReliabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_chinese_font()

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(plt.close, "all")

    def assert_png(self, path):
        self.assertTrue(path.is_file())
        with Image.open(path) as image:
            self.assertEqual(image.format, "PNG")
            image.verify()

    def test_all_five_charts_create_missing_directory(self):
        data = add_analysis_columns(make_data())
        functions = [
            (plot_content_type_comparison, "01_films_vs_tv_average_views.png"),
            (plot_language_comparison, "02_english_vs_non_english_average_views.png"),
            (plot_top_titles, "03_top10_longest_stay_titles.png"),
            (plot_weekly_hours_trend, "04_weekly_total_hours_trend.png"),
            (plot_correlation_distribution, "05_continuous_run_correlation_distribution.png"),
        ]
        for function, filename in functions:
            with self.subTest(function=function.__name__):
                target = Path(self.directory.name) / function.__name__ / "nested"
                self.assertFalse(target.exists())
                # 同時驗證字串路徑；輸出仍是 Path。
                result = function(data, charts_dir=str(target))
                self.assertEqual(result, target / filename)
                self.assert_png(result)
                self.assertEqual(list(target.iterdir()), [result])

    def test_zero_segment_chart_shows_message_without_statistics(self):
        data_cases = [make_data().iloc[:0], make_data((None,) * 6),
                      make_data((100,) * 6), make_data((300, 200, 100))]
        for i, data in enumerate(data_cases):
            with self.subTest(case=i):
                target = Path(self.directory.name) / str(i)
                # 在正常存檔與關閉前檢查實際 figure，確保沒有假統計圖。
                real_close = plt.close

                def inspect_and_close(*args, **kwargs):
                    ax = plt.gcf().axes[0]
                    text = " ".join(t.get_text() for t in ax.texts)
                    self.assertIn("無符合條件資料", text)
                    self.assertIn("有效區段：0", text)
                    self.assertNotIn("nan", text.lower())
                    self.assertNotIn("%", text)
                    self.assertEqual(len(ax.patches), 0)
                    self.assertEqual(len(ax.lines), 0)
                    self.assertFalse(ax.axison)
                    real_close(*args, **kwargs)

                with patch("scripts.visualize.plt.close", side_effect=inspect_and_close):
                    result = plot_correlation_distribution(data, charts_dir=target)
                self.assert_png(result)


if __name__ == "__main__":
    unittest.main()
