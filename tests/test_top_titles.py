from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from scripts.analyze_data import analyze_top_titles
from scripts.visualize import configure_chinese_font, format_top_title_label, plot_top_titles


def make_data():
    return pd.DataFrame([
        ["TV (English)", "Example", "Example: Season 1", 4],
        ["TV (English)", "Example", "Example: Season 1", 7],
        ["TV (English)", "Example", "Example: Season 2", 5],
        ["Films (English)", "Example", "Not specified", 6],
        ["TV (Non-English)", "Unknown", None, 3],
        ["Films (Non-English)", "Special", "Special: Part 1 / Part 2", 2],
    ], columns=["category", "show_title", "season_title", "cumulative_weeks_in_top_10"])


class TopTitlesTests(unittest.TestCase):
    def test_seasons_separate_using_max_not_sum(self):
        result = analyze_top_titles(make_data())
        tv = result[(result.category == "TV (English)") & (result.show_title == "Example")]
        self.assertEqual(tv.season_title.tolist(), ["Example: Season 1", "Example: Season 2"])
        self.assertEqual(tv.cumulative_weeks_in_top_10.tolist(), [7, 5])
        self.assertNotIn(11, result.cumulative_weeks_in_top_10.tolist())
        self.assertNotIn(12, result.cumulative_weeks_in_top_10.tolist())

    def test_same_name_different_categories_separate(self):
        data = make_data()
        extra = pd.DataFrame([["Films (Non-English)", "Example", "Not specified", 8]], columns=data.columns)
        result = analyze_top_titles(pd.concat([data, extra], ignore_index=True))
        films = result[result.category.str.startswith("Films") & result.show_title.eq("Example")]
        self.assertEqual(len(films), 2)
        self.assertEqual(films.cumulative_weeks_in_top_10.tolist(), [8, 6])
        self.assertNotEqual(format_top_title_label(films.iloc[0]), format_top_title_label(films.iloc[1]))

    def test_missing_season_preserved_without_guessing(self):
        for missing in [None, "Not specified"]:
            with self.subTest(missing=missing):
                data = make_data()
                data.loc[data.show_title.eq("Unknown"), "season_title"] = missing
                result = analyze_top_titles(data)
                item = result[result.show_title.eq("Unknown")].iloc[0]
                self.assertEqual(item.cumulative_weeks_in_top_10, 3)
                label = format_top_title_label(item)
                self.assertIn("Unknown（季度未標示）", label)
                self.assertNotIn("Season 1", label)

    def test_official_labels_and_film_categories_preserved(self):
        result = analyze_top_titles(make_data())
        season = result[result.season_title.eq("Example: Season 1")].iloc[0]
        self.assertIn("Example（Season 1）", format_top_title_label(season))
        special = result[result.show_title.eq("Special")].iloc[0]
        self.assertEqual(special.category, "Films (Non-English)")
        self.assertEqual(special.season_title, "Special: Part 1 / Part 2")
        self.assertIn("Special（Part 1 / Part 2）", format_top_title_label(special))
        season = season.copy()
        season["season_title"] = "Example 4"
        self.assertIn("Example（Example 4）", format_top_title_label(season))

    def test_ties_have_reproducible_order(self):
        data = make_data()
        data["cumulative_weeks_in_top_10"] = 5
        expected = analyze_top_titles(data)
        for seed in [1, 2, 3]:
            pd.testing.assert_frame_equal(expected, analyze_top_titles(data.sample(frac=1, random_state=seed)))
        self.assertEqual(expected.iloc[0].category, "Films (English)")
        self.assertEqual(expected.iloc[1].season_title, "Example: Season 1")

    def test_top_n_and_structure(self):
        result = analyze_top_titles(make_data(), top_n=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.columns.tolist(), [
            "category", "show_title", "season_title", "cumulative_weeks_in_top_10"
        ])
        self.assertTrue(analyze_top_titles(make_data(), top_n=0).empty)

    def test_input_unchanged(self):
        data = make_data()
        before = data.copy(deep=True)
        analyze_top_titles(data)
        pd.testing.assert_frame_equal(data, before)

    def test_chart_saves_with_item_labels(self):
        configure_chinese_font()
        data = make_data()
        expected = analyze_top_titles(data)
        captured = {}
        real_savefig = plt.savefig

        def inspect_and_save(*args, **kwargs):
            ax = plt.gcf().axes[0]
            captured["labels"] = [label.get_text() for label in ax.get_yticklabels()]
            captured["widths"] = [bar.get_width() for bar in ax.patches]
            self.assertIn("上榜項目最大累積週數", ax.get_title())
            self.assertIn("最大值", ax.get_xlabel())
            real_savefig(*args, **kwargs)

        with TemporaryDirectory() as folder:
            try:
                with patch("scripts.visualize.plt.savefig", side_effect=inspect_and_save):
                    result = plot_top_titles(data, charts_dir=Path(folder) / "new")
                self.assertEqual(result.name, "03_top10_longest_stay_titles.png")
                with Image.open(result) as image:
                    self.assertEqual(image.format, "PNG")
                    image.verify()
                self.assertEqual(captured["widths"], expected.cumulative_weeks_in_top_10.iloc[::-1].tolist())
                self.assertIn("Example（Season 1）\n[TV (English)]", captured["labels"])
                self.assertIn("Example\n[Films (English)]", captured["labels"])
                self.assertIn("Unknown（季度未標示）\n[TV (Non-English)]", captured["labels"])
                self.assertIn("Special（Part 1 / Part 2）\n[Films (Non-English)]", captured["labels"])
                self.assertEqual(len(captured["labels"]), len(set(captured["labels"])))
            finally:
                plt.close("all")


if __name__ == "__main__":
    unittest.main()
