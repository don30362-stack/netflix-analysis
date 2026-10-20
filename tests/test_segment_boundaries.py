import unittest

import pandas as pd

from scripts.analyze_data import build_consecutive_segments, calculate_segment_correlations


def make_observations(views, category="TV (English)", season="Season 1"):
    return pd.DataFrame({
        "week": pd.date_range("2026-01-04", periods=len(views), freq="7D"),
        "category": [category] * len(views),
        "show_title": ["Offline Same Name"] * len(views),
        "season_title": [season] * len(views),
        "runtime": [2.0] * len(views),
        "weekly_views": views,
        "cumulative_weeks_in_top_10": range(1, len(views) + 1),
    })


class SegmentBoundaryTests(unittest.TestCase):
    def test_adjacent_seven_day_observations_share_one_segment(self):
        data = make_observations([500, 400, 300, 200, 100]).sample(frac=1, random_state=7)
        segments = build_consecutive_segments(data)
        self.assertEqual(segments.streak_id.tolist(), [1] * 5)
        self.assertEqual(segments.streak_week.tolist(), [1, 2, 3, 4, 5])
        self.assertTrue(segments.week.diff().dropna().eq(pd.Timedelta(days=7)).all())
        self.assertEqual(len(calculate_segment_correlations(segments)), 1)

    def test_fourteen_day_gap_starts_a_new_segment(self):
        data = make_observations([500, 400, 300, 200, 100])
        data.loc[2:, "week"] += pd.Timedelta(days=7)
        segments = build_consecutive_segments(data)
        self.assertEqual(segments.streak_id.tolist(), [1, 1, 2, 2, 2])
        self.assertEqual(segments.streak_week.tolist(), [1, 2, 1, 2, 3])
        self.assertTrue(calculate_segment_correlations(segments).empty)

    def test_missing_views_inside_chart_run_splits_valid_observations(self):
        data = make_observations([700, 600, None, 400, 300, 200, 100])
        # 原始紀錄每週都有上榜；目前定義仍以 views 有效的相鄰週切段。
        self.assertTrue(data.week.diff().dropna().eq(pd.Timedelta(days=7)).all())
        segments = build_consecutive_segments(data)
        self.assertEqual(segments.streak_id.tolist(), [1, 1, 2, 2, 2, 2])
        self.assertEqual(segments.streak_week.tolist(), [1, 2, 1, 2, 3, 4])
        self.assertNotIn(data.week.iloc[2], segments.week.tolist())
        self.assertTrue(calculate_segment_correlations(segments).empty)

    def test_missing_prefix_uses_five_observed_weeks_not_full_lifecycle(self):
        data = make_observations([None, None, 500, 400, 300, 200, 100])
        segments = build_consecutive_segments(data)
        self.assertEqual(segments.week.tolist(), data.week.iloc[2:].tolist())
        self.assertEqual(segments.streak_week.tolist(), [1, 2, 3, 4, 5])
        self.assertEqual(segments.cumulative_weeks_in_top_10.tolist(), [3, 4, 5, 6, 7])
        result = calculate_segment_correlations(segments)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.weeks.iloc[0], 5)
        self.assertAlmostEqual(result.pearson.iloc[0], -1.0)
        self.assertAlmostEqual(result.spearman.iloc[0], -1.0)

    def test_tv_runtime_change_does_not_split_same_season(self):
        data = make_observations([500, 400, 300, 200, 100])
        data["runtime"] = [1.0, 2.0, 3.0, 3.0, 3.0]
        segments = build_consecutive_segments(data)
        self.assertEqual(segments.analysis_unit.nunique(), 1)
        self.assertEqual(segments.streak_id.tolist(), [1] * 5)
        self.assertEqual(len(calculate_segment_correlations(segments)), 1)

    def test_seasons_and_categories_are_separate_analysis_units(self):
        views = [500, 400, 300, 200, 100]
        data = pd.concat([
            make_observations(views, season="Season 1"),
            make_observations(views, season="Season 2"),
            make_observations(views, category="TV (Non-English)", season="Season 1"),
            make_observations(views, category="Films (English)", season="Not specified"),
        ], ignore_index=True)
        segments = build_consecutive_segments(data)
        result = calculate_segment_correlations(segments)
        self.assertEqual(segments.analysis_unit.nunique(), 4)
        self.assertEqual(len(result), 4)
        self.assertEqual(result.weeks.tolist(), [5] * 4)
        for _, group in segments.groupby("analysis_unit"):
            self.assertEqual(group.streak_week.tolist(), [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
