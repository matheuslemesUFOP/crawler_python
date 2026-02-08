from pathlib import Path
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
class Crawler:
    """Crawler for web data extraction with region filter."""

    def __init__(self, headless: bool = True) -> None:
        """
        Initialize the crawler.

        Args:
            headless: If True, runs the browser in headless mode (no UI).
        """
        self._headless = headless
        self._driver: Optional[webdriver.Chrome] = None

    def _get_driver(self) -> webdriver.Chrome:
        """Return the Selenium WebDriver (reuses existing instance if any)."""
        if self._driver is None:
            options = Options()
            if self._headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            self._driver = webdriver.Chrome(options=options)
        return self._driver

    def extract(self, url: str, region: str) -> pd.DataFrame:
        """
        Fetch the URL, extract data and filter by region.

        Args:
            url: Page URL to extract data from.
            region: Value used as filter (e.g. region name, code).

        Returns:
            DataFrame with columns: symbol, name, price (data filtered by region).
        """
        driver = self._get_driver()
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        rows: list[dict] = []

        # Try to extract from tables (tr with td: symbol, name, price)
        for tr in soup.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) >= 3:
                symbol = (cells[0].get_text(strip=True) or "").strip()
                name = (cells[1].get_text(strip=True) or "").strip()
                price = (cells[2].get_text(strip=True) or "").strip()
                if region.lower() in name.lower() or region.lower() in symbol.lower():
                    rows.append({"symbol": symbol, "name": name, "price": price})

        # Fallback: links (name = text, symbol/price empty)
        if not rows:
            for anchor in soup.find_all("a", href=True):
                name = (anchor.get_text(strip=True) or "").strip()
                if not name or not anchor.get("href", "").strip() or anchor.get("href", "").strip().startswith("#"):
                    continue
                if region.lower() in name.lower():
                    rows.append({"symbol": "", "name": name, "price": ""})

        df = pd.DataFrame(rows, columns=["symbol", "name", "price"])
        return df

    def export_csv(self, df: pd.DataFrame, path: str | Path) -> Path:
        """
        Export the DataFrame to a CSV file.

        Args:
            df: DataFrame returned by extract() (or any DataFrame).
            path: Output CSV file path.

        Returns:
            Path of the generated file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def close(self) -> None:
        """Close the browser and release resources."""
        if self._driver is not None:
            self._driver.quit()
            self._driver = None

    def __enter__(self) -> "Crawler":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
