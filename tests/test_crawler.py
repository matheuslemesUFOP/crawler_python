"""
Unit tests for the Crawler class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from crawler import Crawler


class TestParsePrice:
    """Tests for _parse_price."""

    def test_valid_with_comma(self, crawler: Crawler) -> None:
        assert crawler._parse_price("11,520.00") == 11520.0

    def test_valid_no_comma(self, crawler: Crawler) -> None:
        assert crawler._parse_price("150.25") == 150.25

    def test_empty_string(self, crawler: Crawler) -> None:
        assert crawler._parse_price("") == 0.0

    def test_invalid_returns_zero(self, crawler: Crawler) -> None:
        assert crawler._parse_price("not a number") == 0.0

    def test_whitespace_only(self, crawler: Crawler) -> None:
        assert crawler._parse_price("   ") == 0.0


class TestGetTableRows:
    """Tests for _get_table_rows."""

    def test_returns_rows_when_structure_present(
        self, crawler: Crawler, html_with_table: str
    ) -> None:
        rows = crawler._get_table_rows(html_with_table)
        assert len(rows) == 3
        assert all(r.name == "tr" for r in rows)

    def test_returns_empty_when_no_screener_div(
        self, crawler: Crawler, html_total_only: str
    ) -> None:
        rows = crawler._get_table_rows(html_total_only)
        assert rows == []

    def test_returns_empty_for_empty_html(
        self, crawler: Crawler, html_empty: str
    ) -> None:
        rows = crawler._get_table_rows(html_empty)
        assert rows == []


class TestGetTotalRows:
    """Tests for _get_total_rows."""

    def test_extracts_total_from_div(self, crawler: Crawler, html_total_only: str) -> None:
        assert crawler._get_total_rows(html_total_only) == 1067

    def test_returns_zero_when_no_div(self, crawler: Crawler, html_empty: str) -> None:
        assert crawler._get_total_rows(html_empty) == 0

    def test_returns_zero_when_no_of_in_text(self, crawler: Crawler) -> None:
        html = '<div class="total yf-c259ju">invalid</div>'
        assert crawler._get_total_rows(html) == 0


class TestGetRowsPerPage:
    """Tests for _get_rows_per_page."""

    def test_extracts_from_aria_label(
        self, crawler: Crawler, html_rows_per_page_button: str
    ) -> None:
        assert crawler._get_rows_per_page(html_rows_per_page_button) == 25

    def test_returns_zero_when_no_button(self, crawler: Crawler, html_empty: str) -> None:
        assert crawler._get_rows_per_page(html_empty) == 0


class TestParseTableRows:
    """Tests for _parse_table_rows."""

    def test_parses_rows_to_dicts(self, crawler: Crawler, html_with_table: str) -> None:
        rows_html = crawler._get_table_rows(html_with_table)
        result = crawler._parse_table_rows(rows_html)
        assert len(result) == 3
        assert result[0] == {"symbol": "AAPL", "name": "Apple Inc", "price": 150.25}
        assert result[1] == {"symbol": "MSFT", "name": "Microsoft", "price": 11520.0}
        assert result[2] == {"symbol": "GOOG", "name": "Alphabet", "price": 140.5}

    def test_skips_rows_with_fewer_than_five_cells(self, crawler: Crawler) -> None:
        soup = BeautifulSoup(
            "<tr><td>a</td><td>b</td></tr>",
            "html.parser",
        )
        result = crawler._parse_table_rows(soup.find_all("tr"))
        assert result == []

    def test_returns_empty_for_empty_list(self, crawler: Crawler) -> None:
        assert crawler._parse_table_rows([]) == []


class TestIsLastPage:
    """Tests for is_last_page."""

    def test_last_page_when_all_items_fit(self, crawler: Crawler) -> None:
        assert crawler.is_last_page(0, 25, 25) is True
        assert crawler.is_last_page(0, 10, 25) is True

    def test_not_last_page_when_more_pages(self, crawler: Crawler) -> None:
        assert crawler.is_last_page(0, 1067, 25) is False
        assert crawler.is_last_page(10, 1067, 25) is False

    def test_last_page_on_final_page(self, crawler: Crawler) -> None:
        # 1067 rows, 25 per page -> 43 pages (0-42). Page 42 is last.
        assert crawler.is_last_page(42, 1067, 25) is True
        assert crawler.is_last_page(41, 1067, 25) is False

    def test_rows_per_page_zero_returns_true(self, crawler: Crawler) -> None:
        assert crawler.is_last_page(0, 100, 0) is True


class TestExportCsv:
    """Tests for export_csv."""

    def test_writes_file_and_returns_path(
        self, crawler: Crawler, tmp_path: Path
    ) -> None:
        df = pd.DataFrame(
            [{"symbol": "A", "name": "B", "price": 1.0}],
            columns=["symbol", "name", "price"],
        )
        out = tmp_path / "out" / "file.csv"
        path = crawler.export_csv(df, out)
        assert path == out
        assert path.exists()
        content = path.read_text(encoding="utf-8-sig")
        assert "symbol" in content
        assert "A" in content

    def test_creates_parent_dirs(self, crawler: Crawler, tmp_path: Path) -> None:
        df = pd.DataFrame(columns=["symbol", "name", "price"])
        out = tmp_path / "deep" / "dir" / "file.csv"
        crawler.export_csv(df, out)
        assert out.exists()


class TestCrawlerInitAndClose:
    """Tests for init and close."""

    def test_context_manager_closes_driver(self) -> None:
        with patch.object(Crawler, "_get_driver") as get_driver:
            mock_driver = MagicMock()
            get_driver.return_value = mock_driver
            c = Crawler(headless=True)
            c._driver = mock_driver
            c.close()
            mock_driver.quit.assert_called_once()
            assert c._driver is None

    def test_enter_exit_returns_self(self) -> None:
        c = Crawler(headless=True)
        with patch.object(c, "close"):
            assert c.__enter__() is c
            c.__exit__(None, None, None)
            c.close.assert_called_once()


class TestExtract:
    """Tests for extract with mocked driver."""

    @pytest.fixture
    def html_single_page(self) -> str:
        """One page only (total 3) so extract runs one iteration."""
        return """
        <div class="screener-table yf-hm80y7">
            <div class="total yf-c259ju">1-3 of 3</div>
            <table class="yf-1uayyp1 bd">
                <tbody>
                    <tr><td>0</td><td>A</td><td>Name A</td><td>x</td><td>10.0</td></tr>
                    <tr><td>1</td><td>B</td><td>Name B</td><td>x</td><td>20.0</td></tr>
                    <tr><td>2</td><td>C</td><td>Name C</td><td>x</td><td>30.0</td></tr>
                </tbody>
            </table>
        </div>
        """

    @pytest.fixture
    def mock_driver(self, html_single_page: str) -> MagicMock:
        driver = MagicMock()
        driver.page_source = html_single_page
        return driver

    @patch("crawler.crawler.time.sleep")
    def test_extract_returns_dataframe_with_expected_columns(
        self, mock_sleep: MagicMock, crawler: Crawler, mock_driver: MagicMock
    ) -> None:
        with patch.object(crawler, "_get_driver", return_value=mock_driver):
            df = crawler.extract("https://example.com", "Argentina")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["symbol", "name", "price"]
        assert len(df) == 3
        assert df["symbol"].tolist() == ["A", "B", "C"]

    @patch("crawler.crawler.time.sleep")
    def test_extract_calls_driver_get(
        self, mock_sleep: MagicMock, crawler: Crawler, mock_driver: MagicMock
    ) -> None:
        with patch.object(crawler, "_get_driver", return_value=mock_driver):
            crawler.extract("https://example.com/screener", "Brazil")
        mock_driver.get.assert_called_once_with("https://example.com/screener")
