"""
Unit tests for main.Application and configuration.
"""

import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

# Import after potential env setup so load_dotenv can be patched
from main import Application


class TestApplicationLoadConfig:
    """Tests for Application._load_config (via __init__)."""

    def test_requires_crawler_url(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("main.load_dotenv"):
                with pytest.raises(SystemExit):
                    Application()

    def test_sets_url_region_and_output_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CRAWLER_URL": "https://finance.yahoo.com/screener",
                "CRAWLER_REGION": "Argentina",
                "CRAWLER_OUTPUT": "out_ar.csv",
            },
            clear=False,
        ):
            with patch("main.load_dotenv"):
                app = Application()
        assert app._url == "https://finance.yahoo.com/screener"
        assert app._region == "Argentina"
        assert app._output_path == "out_ar.csv"

    def test_default_region_when_not_set(self) -> None:
        with patch.dict(
            os.environ,
            {"CRAWLER_URL": "https://example.com"},
            clear=False,
        ):
            with patch("main.load_dotenv"):
                app = Application()
        assert app._region == "Brazil"

    def test_strips_whitespace_from_url(self) -> None:
        with patch.dict(
            os.environ,
            {"CRAWLER_URL": "  https://example.com  "},
            clear=False,
        ):
            with patch("main.load_dotenv"):
                app = Application()
        assert app._url == "https://example.com"


class TestApplicationRun:
    """Tests for Application.run with mocked Crawler."""

    @pytest.fixture
    def app_with_config(self) -> Application:
        with patch.dict(
            os.environ,
            {"CRAWLER_URL": "https://example.com", "CRAWLER_REGION": "Brazil"},
            clear=False,
        ):
            with patch("main.load_dotenv"):
                return Application()

    def test_run_calls_extract_and_export_csv(
        self, app_with_config: Application
    ) -> None:
        import pandas as pd

        fake_df = pd.DataFrame(
            [{"symbol": "X", "name": "Y", "price": 1.0}],
            columns=["symbol", "name", "price"],
        )
        with patch("main.Crawler") as MockCrawler:
            mock_crawler_instance = MockCrawler.return_value
            mock_crawler_instance.__enter__ = lambda self: self
            mock_crawler_instance.__exit__ = lambda *args: None
            mock_crawler_instance.extract.return_value = fake_df
            mock_crawler_instance.export_csv.return_value = __import__(
                "pathlib"
            ).Path("output_Brazil.csv")
            with patch("sys.stdout", new_callable=StringIO):
                app_with_config.run()
            mock_crawler_instance.extract.assert_called_once_with(
                app_with_config._url, app_with_config._region
            )
            mock_crawler_instance.export_csv.assert_called_once()

    def test_run_prints_result(self, app_with_config: Application) -> None:
        import pandas as pd

        fake_df = pd.DataFrame(
            [{"symbol": "A", "name": "B", "price": 1.0}],
            columns=["symbol", "name", "price"],
        )
        with patch("main.Crawler") as MockCrawler:
            mock_crawler_instance = MockCrawler.return_value
            mock_crawler_instance.__enter__ = lambda self: self
            mock_crawler_instance.__exit__ = lambda *args: None
            mock_crawler_instance.extract.return_value = fake_df
            mock_crawler_instance.export_csv.return_value = __import__(
                "pathlib"
            ).Path("out.csv")
            out = StringIO()
            with patch("sys.stdout", out):
                app_with_config.run()
            assert "1 record(s)" in out.getvalue()
            assert "out.csv" in out.getvalue()
