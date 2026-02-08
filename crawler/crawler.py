import time
from pathlib import Path
from typing import List, Optional

import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

    def _click_region_menu_button(self, driver: webdriver.Chrome, timeout: int = 10) -> None:
        """
        Click the 'Region' (menuBtn) button that opens the region filter dropdown.
        Uses the button with menuBtn class that contains the text 'Region'.
        """
        wait = WebDriverWait(driver, timeout)
        try:
            region_btn = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@class, 'menuBtn') and .//div[text()='Region']]"
                ))
            )
            region_btn.click()
            time.sleep(1)
        except Exception:
            try:
                # Fallback: by data-ylk attribute containing 'Region'
                region_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "button.menuBtn[data-ylk*='Region']"
                )
                region_btn.click()
                time.sleep(1)
            except Exception:
                pass

    def _select_region_from_options_and_apply(self, driver: webdriver.Chrome, region: str, timeout: int = 10) -> None:
        """
        Within the Region menu, ensure only the desired region is selected:
        uncheck all options, check only the given region, and click Apply.
        """
        wait = WebDriverWait(driver, timeout)
        try:
            wait.until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    "div.yf-19pw8k1.options, div.options"
                ))
            )
        except Exception:
            pass

        # Uncheck all currently selected regions (ensure only the desired one remains checked)
        try:
            options_div = driver.find_element(
                By.XPATH,
                "//div[contains(@class,'options')]"
            )
            checkboxes = options_div.find_elements(By.CSS_SELECTOR, "input[type=checkbox]")
            for cb in checkboxes:
                try:
                    if cb.is_selected():
                        # Click parent label to uncheck (input may be hidden)
                        label_el = cb.find_element(By.XPATH, "..")
                        label_el.click()
                        time.sleep(0.1)
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(0.2)

        # Check only the desired region (title or aria-label equal to region)
        region_escaped = region.replace("'", "\\'")
        selectors = [
            f"//div[contains(@class,'options')]//label[@title='{region_escaped}' or @aria-label='{region_escaped}']",
            f"//div[contains(@class,'options')]//label[.//span[normalize-space(text())='{region_escaped}']]",
        ]
        clicked = False
        for xpath in selectors:
            try:
                label_el = wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                label_el.click()
                clicked = True
                time.sleep(0.3)
                break
            except Exception:
                continue
        if not clicked:
            return

        # Click Apply (button with aria-label="Apply" and class primary-btn)
        try:
            apply_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Apply']"))
            )
            apply_btn.click()
            time.sleep(2)
        except Exception:
            try:
                apply_btn = driver.find_element(
                    By.XPATH,
                    "//button[contains(@class,'primary-btn') and @aria-label='Apply']"
                )
                apply_btn.click()
                time.sleep(2)
            except Exception:
                pass

    def _parse_price(self, price_str: str) -> float:
        """
        Convert price string (e.g. '11,520.00') to float.
        Removes commas; returns 0.0 on invalid value.
        """
        if not price_str:
            return 0.0
        try:
            return float(price_str.replace(",", ""))
        except ValueError:
            return 0.0

    def _get_table_rows(self, html: str) -> List[Tag]:
        """
        Extract table rows (tr) from the screener HTML.
        Looks for div.screener-table, table.bd, tbody and returns list of tr.
        Returns empty list if structure is not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        div_table = soup.find_all("div", class_="screener-table yf-hm80y7")
        if not div_table:
            return []
        table = div_table[0].find("table", class_="yf-1uayyp1 bd")
        if not table:
            return []
        tbody = table.find("tbody")
        if not tbody:
            return []
        return tbody.find_all("tr")

    def _get_total_rows(self, html: str) -> int:
        """
        Extract total row count from div with class 'total yf-c259ju'.
        Text format is '1-25 of 1067'; returns the number after ' of ' (e.g. 1067).
        Returns 0 if not found or parse fails.
        """
        soup = BeautifulSoup(html, "html.parser")
        div_total = soup.find("div", class_="total yf-c259ju")
        if not div_total:
            return 0
        text = div_total.get_text(strip=True) or ""
        if " of " not in text:
            return 0
        try:
            return int(text.split(" of ")[-1].strip())
        except (ValueError, IndexError):
            return 0

    def _get_rows_per_page(self, html: str) -> int:
        """
        Extract rows-per-page value from the menu button (e.g. 25).
        Button has menuBtn class, aria-label/title with the number and a span with the text.
        Returns 0 if not found or parse fails.
        """
        soup = BeautifulSoup(html, "html.parser")
        btn = soup.find(
            "button",
            class_=lambda c: c and "menuBtn" in (c or "") and "rightAlign" in (c or "")
        )
        if not btn:
            btn = soup.find("button", attrs={"aria-label": True, "title": True})
        if not btn:
            return 0
        for attr in ("aria-label", "title"):
            val = btn.get(attr)
            if val:
                try:
                    return int(str(val).strip())
                except ValueError:
                    pass
        span = btn.find("span", class_=lambda c: c and "textSelect" in (c or ""))
        if span:
            try:
                return int(span.get_text(strip=True))
            except ValueError:
                pass
        return 0

    def is_last_page(self, page: int, total_rows: int, rows_per_page: int) -> bool:
        """
        Return True if we are on the last pagination page (should not click Next).
        page is 0-based; total_rows is total items; rows_per_page is items per page.
        """
        if rows_per_page <= 0:
            return True
        return (page + 1) * rows_per_page >= total_rows

    def click_next_page(self, driver: webdriver.Chrome, timeout: int = 10) -> None:
        """
        Click the 'Next' pagination button on the screener (Yahoo Finance).
        Uses data-testid='next-page-button' and aria-label='Goto next page'.
        """
        wait = WebDriverWait(driver, timeout)
        selectors = [
            (By.CSS_SELECTOR, "button[data-testid='next-page-button']"),
            (By.XPATH, "//button[@data-testid='next-page-button']"),
            (By.XPATH, "//button[@aria-label='Goto next page']"),
            (By.CSS_SELECTOR, "button[aria-label='Goto next page']"),
        ]
        for by, selector in selectors:
            try:
                btn = wait.until(EC.element_to_be_clickable((by, selector)))
                btn.click()
                time.sleep(2)
                return
            except Exception:
                continue

    def filter_region(self, driver: webdriver.Chrome, region: str) -> None:
        """
        Apply the region filter: open the Region menu, select the desired region and click Apply.
        """
        self._click_region_menu_button(driver)
        time.sleep(1)
        self._select_region_from_options_and_apply(driver, region)

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
        self.filter_region(driver, region)

        html = driver.page_source
        total_rows = self._get_total_rows(html)
        rows_per_page = self._get_rows_per_page(html)
        rows: list[dict] = []
        page = 0
        
        while True:
            rows_html = self._get_table_rows(html)
            if not rows_per_page:
                rows_per_page = len(rows_html)
            if rows_per_page == 0:
                break
            for tr_html in rows_html:
                cells_html = tr_html.find_all("td")
                symbol = cells_html[1].get_text(strip=True) or ""
                name = cells_html[2].get_text(strip=True) or ""
                price_str = cells_html[4].get_text(strip=True) or ""
                price = self._parse_price(price_str)
                rows.append({"symbol": symbol, "name": name, "price": price})
            if self.is_last_page(page, total_rows, rows_per_page):
                break
            self.click_next_page(driver)
            html = driver.page_source
            page += 1

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
