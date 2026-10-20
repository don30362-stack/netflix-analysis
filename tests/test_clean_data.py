import unittest

import pandas as pd

from scripts.analyze_data import analyze_weekly_trend
from scripts.clean_data import clean_netflix_data


def make_data():
    return pd.DataFrame({
        "week": ["2026-01-04", "2026-01-11"],
        "category": ["TV (English)"] * 2,
        "weekly_rank": [1, 1],
        "show_title": ["Offline Show"] * 2,
        "season_title": ["Season 1"] * 2,
        "weekly_hours_viewed": [1000, 800],
        "runtime": [2.0, 2.0],
        "weekly_views": [500.0, 400.0],
        "cumulative_weeks_in_top_10": [1, 2],
    })


class CleanDataValidationTests(unittest.TestCase):
    def test_valid_data_and_input_unchanged(self):
        raw = make_data()
        original = raw.copy(deep=True)
        cleaned = clean_netflix_data(raw)
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(cleaned.week))
        self.assertEqual(cleaned.weekly_hours_viewed.tolist(), [1000, 800])
        pd.testing.assert_frame_equal(raw, original)

    def test_empty_data_rejected(self):
        with self.assertRaisesRegex(ValueError, "不可為空：0 筆"):
            clean_netflix_data(make_data().iloc[:0])

    def test_missing_columns_rejected(self):
        with self.assertRaisesRegex(ValueError, "缺少必要欄位（2 個）.*category, runtime"):
            clean_netflix_data(make_data().drop(columns=["runtime", "category"]))

    def test_missing_key_values_rejected(self):
        for column in ["week", "category", "weekly_rank", "show_title",
                       "weekly_hours_viewed", "cumulative_weeks_in_top_10"]:
            with self.subTest(column=column):
                data = make_data().astype({column: object})
                data.loc[0, column] = None
                with self.assertRaisesRegex(ValueError, f"{column} .*：1 筆"):
                    clean_netflix_data(data)

    def test_invalid_date_and_blank_titles_rejected(self):
        for column, value in [("week", "2026-02-30"), ("show_title", "   "), ("category", "")]:
            with self.subTest(column=column):
                data = make_data()
                data.loc[1, column] = value
                with self.assertRaisesRegex(ValueError, f"{column} .*：1 筆"):
                    clean_netflix_data(data)

    def test_invalid_category_rank_and_negative_values_rejected(self):
        for column, values in {
            "category": ["Films", "TV (Unknown)"],
            "weekly_rank": [0, 11, -1],
            "weekly_hours_viewed": [-1],
            "weekly_views": [-1],
            "cumulative_weeks_in_top_10": [0, -1],
        }.items():
            for value in values:
                with self.subTest(column=column, value=value):
                    data = make_data().astype({column: object})
                    data.loc[0, column] = value
                    with self.assertRaisesRegex(ValueError, f"{column} .*：1 筆"):
                        clean_netflix_data(data)

    def test_infinite_and_fractional_integer_fields_rejected(self):
        for column in ["weekly_rank", "weekly_hours_viewed", "weekly_views",
                       "runtime", "cumulative_weeks_in_top_10"]:
            for value in [float("inf"), -float("inf")]:
                with self.subTest(column=column, value=value):
                    data = make_data().astype({column: object})
                    data.loc[0, column] = value
                    with self.assertRaisesRegex(ValueError, f"{column} 必須是有限數值：1 筆"):
                        clean_netflix_data(data)
        for column in ["weekly_rank", "cumulative_weeks_in_top_10"]:
            data = make_data().astype({column: object})
            data.loc[0, column] = 1.5
            with self.subTest(column=column):
                with self.assertRaisesRegex(ValueError, f"{column} 必須是.*整數：1 筆"):
                    clean_netflix_data(data)

    def test_non_numeric_content_is_not_silently_missing(self):
        for column in ["weekly_rank", "weekly_hours_viewed", "weekly_views",
                       "runtime", "cumulative_weeks_in_top_10"]:
            with self.subTest(column=column):
                data = make_data().astype({column: object})
                data.loc[0, column] = "invalid"
                with self.assertRaisesRegex(ValueError, f"{column} 無法轉為數值：1 筆"):
                    clean_netflix_data(data)

    def test_rank_conflict_rejected(self):
        data = make_data()
        data.loc[1, "week"] = data.loc[0, "week"]
        data.loc[1, "show_title"] = "Other Show"
        with self.assertRaisesRegex(ValueError, "同週同類別排名衝突：1 組，涉及 2 筆"):
            clean_netflix_data(data)

    def test_same_item_with_different_rank_rejected(self):
        data = make_data()
        data.loc[1, "week"] = data.loc[0, "week"]
        data.loc[1, "weekly_rank"] = 2
        with self.assertRaisesRegex(ValueError, "同週同類別作品及季度重複：1 組，涉及 2 筆"):
            clean_netflix_data(data)

    def test_different_seasons_same_week_preserved(self):
        data = make_data()
        data.loc[1, "week"] = data.loc[0, "week"]
        data.loc[1, "weekly_rank"] = 2
        data.loc[1, "season_title"] = "Season 2"
        self.assertEqual(len(clean_netflix_data(data)), 2)

    def test_same_film_name_different_categories_preserved(self):
        data = make_data()
        data.loc[1, "week"] = data.loc[0, "week"]
        data["category"] = ["Films (English)", "Films (Non-English)"]
        # Films 帶 season_title 合法，不修改官方分類。
        cleaned = clean_netflix_data(data)
        self.assertEqual(cleaned.category.tolist(), data.category.tolist())
        self.assertEqual(cleaned.season_title.tolist(), data.season_title.tolist())

    def test_optional_missing_values_and_nonpositive_runtime_preserved(self):
        data = make_data()
        data["weekly_views"] = [None, None]
        data["runtime"] = [None, 0]
        data["season_title"] = [None, None]
        cleaned = clean_netflix_data(data)
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(cleaned.weekly_views.isna().all())
        self.assertTrue(cleaned.runtime.isna().all())
        self.assertEqual(cleaned.season_title.tolist(), ["Not specified"] * 2)
        data["runtime"] = [-2.0, 1.5]
        cleaned = clean_netflix_data(data)
        self.assertTrue(pd.isna(cleaned.runtime.iloc[0]))
        self.assertEqual(cleaned.runtime.iloc[1], 1.5)

    def test_exact_duplicates_removed(self):
        data = make_data()
        cleaned = clean_netflix_data(pd.concat([data, data.iloc[[0]]], ignore_index=True))
        self.assertEqual(len(cleaned), 2)
        self.assertFalse(cleaned.duplicated().any())

    def test_numeric_strings_converted_and_zero_views_allowed(self):
        data = make_data()
        for column in ["weekly_rank", "weekly_hours_viewed", "weekly_views",
                       "runtime", "cumulative_weeks_in_top_10"]:
            data[column] = data[column].astype(str)
        data.loc[0, "weekly_views"] = "0"
        data.loc[0, "weekly_hours_viewed"] = "0"
        cleaned = clean_netflix_data(data)
        self.assertEqual(cleaned.weekly_views.iloc[0], 0)
        self.assertEqual(cleaned.weekly_hours_viewed.iloc[0], 0)


class WeeklyTrendMissingValueTests(unittest.TestCase):
    def test_all_missing_week_remains_missing(self):
        data = make_data()
        data["week"] = pd.to_datetime(data.week)
        data["weekly_hours_viewed"] = [float("nan"), 800]
        result = analyze_weekly_trend(data)
        self.assertTrue(pd.isna(result["weekly_total_hours"].iloc[0]))
        self.assertEqual(result["min_hours"], 800)
        self.assertEqual(result["min_week"], pd.Timestamp("2026-01-11"))

    def test_no_valid_hours_rejected(self):
        data = make_data()
        data["week"] = pd.to_datetime(data.week)
        data["weekly_hours_viewed"] = float("nan")
        with self.assertRaisesRegex(ValueError, "無法分析趨勢：2 週有效值為 0 筆"):
            analyze_weekly_trend(data)

    def test_normal_weekly_sums_unchanged(self):
        data = make_data()
        data["week"] = pd.to_datetime(data.week)
        data = pd.concat([data, data], ignore_index=True)
        expected = data.groupby("week").weekly_hours_viewed.sum().sort_index()
        result = analyze_weekly_trend(data)
        pd.testing.assert_series_equal(result["weekly_total_hours"], expected)
        self.assertEqual(result["max_hours"], 2000)
        self.assertEqual(result["min_hours"], 1600)


if __name__ == "__main__":
    unittest.main()
