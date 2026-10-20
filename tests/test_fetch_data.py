from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import pandas as pd
import requests

from scripts.clean_data import REQUIRED_COLUMNS
from scripts.fetch_data import DATA_URL, fetch_netflix_data


def make_excel_bytes(missing_columns=(), show_title="Offline Test Film"):
    row = {
        "week": "2026-08-16",
        "category": "Films (English)",
        "weekly_rank": 1,
        "show_title": show_title,
        "season_title": None,
        "weekly_hours_viewed": 1000,
        "runtime": 2,
        "weekly_views": 500,
        "cumulative_weeks_in_top_10": 1,
    }
    stream = BytesIO()
    pd.DataFrame([row]).drop(columns=list(missing_columns)).to_excel(
        stream, index=False, engine="openpyxl"
    )
    return stream.getvalue()


class FetchNetflixDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_excel = make_excel_bytes()
        cls.missing_columns_excel = make_excel_bytes(("weekly_views", "runtime"))

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output_path = Path(self.directory.name) / "netflix.xlsx"
        # 所有測試一律攔截 HTTP；不需要網路或正式資料。
        self.get_patcher = patch("scripts.fetch_data.requests.get")
        self.mock_get = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)
        self.response = Mock()
        self.response.content = self.valid_excel
        self.mock_get.return_value = self.response

    def assert_old_file_preserved(self):
        self.assertEqual(self.output_path.read_bytes(), self.valid_excel)
        self.assertEqual(list(self.output_path.parent.iterdir()), [self.output_path])

    def test_valid_excel_saved(self):
        result = fetch_netflix_data(output_path=self.output_path)
        self.assertEqual(result, self.output_path)
        self.assert_old_file_preserved()
        self.assertEqual(
            set(pd.read_excel(result, engine="openpyxl").columns), REQUIRED_COLUMNS
        )
        self.mock_get.assert_called_once_with(DATA_URL, timeout=30)
        self.response.raise_for_status.assert_called_once_with()

    def test_valid_excel_replaces_existing_file(self):
        old_excel = make_excel_bytes(show_title="Previous Valid Film")
        self.output_path.write_bytes(old_excel)
        fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_http_error_preserves_old_file(self):
        self.output_path.write_bytes(self.valid_excel)
        self.response.raise_for_status.side_effect = requests.exceptions.HTTPError("503")
        with self.assertRaisesRegex(RuntimeError, "下載 Netflix 資料失敗.*503"):
            fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_timeout_preserves_old_file(self):
        self.output_path.write_bytes(self.valid_excel)
        self.mock_get.side_effect = requests.exceptions.Timeout()
        with self.assertRaisesRegex(RuntimeError, "連線逾時"):
            fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_empty_content_preserves_old_file(self):
        self.output_path.write_bytes(self.valid_excel)
        self.response.content = b""
        with self.assertRaisesRegex(RuntimeError, "空白內容"):
            fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_non_excel_content_preserves_old_file(self):
        self.output_path.write_bytes(self.valid_excel)
        for content in (b"<html>Service unavailable</html>", b"not excel", b"PK\x03\x04broken"):
            with self.subTest(content=content):
                self.response.content = content
                with self.assertRaisesRegex(RuntimeError, "不是可讀取的 Excel"):
                    fetch_netflix_data(output_path=self.output_path)
                self.assert_old_file_preserved()

    def test_missing_columns_preserves_old_file(self):
        self.output_path.write_bytes(self.valid_excel)
        self.response.content = self.missing_columns_excel
        with self.assertRaisesRegex(RuntimeError, "缺少必要欄位：runtime, weekly_views"):
            fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_invalid_content_does_not_create_target_directory(self):
        self.response.content = b"invalid"
        target = self.output_path.parent / "new" / "netflix.xlsx"
        with self.assertRaises(RuntimeError):
            fetch_netflix_data(output_path=target)
        self.assertFalse(target.parent.exists())

    def test_creates_parent_directory(self):
        target = self.output_path.parent / "new" / "netflix.xlsx"
        self.assertEqual(fetch_netflix_data(output_path=target), target)
        self.assertEqual(target.read_bytes(), self.valid_excel)
        self.assertEqual(list(target.parent.iterdir()), [target])

    def test_replace_failure_cleans_temporary_file(self):
        self.output_path.write_bytes(self.valid_excel)

        def fail_replace(source, target):
            self.assertEqual(source.parent, self.output_path.parent)
            self.assertEqual(source.read_bytes(), self.valid_excel)
            self.assertEqual(target, self.output_path)
            raise PermissionError("Target locked")

        with patch("scripts.fetch_data.Path.replace", autospec=True, side_effect=fail_replace):
            with self.assertRaisesRegex(RuntimeError, "儲存 Netflix 資料失敗"):
                fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()

    def test_write_failure_cleans_temporary_file(self):
        self.output_path.write_bytes(self.valid_excel)
        with NamedTemporaryFile(dir=self.output_path.parent, delete=False) as real_file:
            temporary_path = Path(real_file.name)
        file_handle = temporary_path.open("wb")
        wrapped_file = Mock(wraps=file_handle)
        wrapped_file.name = str(temporary_path)

        def fail_write(content):
            file_handle.write(content[:10])
            raise OSError("Disk full")

        wrapped_file.write.side_effect = fail_write
        context = Mock()
        context.__enter__ = Mock(return_value=wrapped_file)
        context.__exit__ = Mock(side_effect=lambda *args: wrapped_file.close())
        with patch("scripts.fetch_data.NamedTemporaryFile", return_value=context):
            with self.assertRaisesRegex(RuntimeError, "儲存 Netflix 資料失敗"):
                fetch_netflix_data(output_path=self.output_path)
        self.assert_old_file_preserved()


if __name__ == "__main__":
    unittest.main()
