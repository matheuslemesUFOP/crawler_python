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

    def _accept_cookies_if_present(self, driver: webdriver.Chrome) -> None:
        """Click cookie consent button so the page can load (e.g. Yahoo Finance)."""
        try:
            accept = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'Accept all')]"))
            )
            accept.click()
        except Exception:
            pass

    def _click_region_menu_button(self, driver: webdriver.Chrome, timeout: int = 10) -> None:
        """
        Clica no botão 'Region' (menuBtn) que abre o dropdown de filtro de região.
        Usa o botão com classe menuBtn que contém o texto 'Region'.
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
                # Alternativa: pelo atributo data-ylk que contém 'Region'
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
        Dentro do menu Region, garante que só a região desejada esteja selecionada:
        desmarca todas as opções, marca apenas a região informada e clica em Apply.
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

        # Desmarcar todas as regiões já selecionadas (garantir que só a desejada fique marcada)
        try:
            options_div = driver.find_element(
                By.XPATH,
                "//div[contains(@class,'options')]"
            )
            checkboxes = options_div.find_elements(By.CSS_SELECTOR, "input[type=checkbox]")
            for cb in checkboxes:
                try:
                    if cb.is_selected():
                        # Clicar no label pai para desmarcar (o input pode estar oculto)
                        label_el = cb.find_element(By.XPATH, "..")
                        label_el.click()
                        time.sleep(0.1)
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(0.2)

        # Marcar somente a região desejada (title ou aria-label igual ao region)
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

        # Clicar em Apply (botão com aria-label="Apply" e class primary-btn)
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

    def _apply_region_filter_on_yahoo(self, driver: webdriver.Chrome, region: str, timeout: int = 15) -> None:
        """
        Apply Region filter on Yahoo Finance screener: click the Region filter chip
        (div.filter.yf-qonzlw with "Region"), then in the modal search and select the region, Apply.
        """
        wait = WebDriverWait(driver, timeout)
        try:
            # Click the Region filter chip: div.filter that contains a div with text "Region"
            region_filter_chip = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class, 'filter') and contains(@class, 'yf-') and .//div[text()='Region']]"
                ))
            )
            region_filter_chip.click()
        except Exception:
            try:
                region_filter_chip = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'filter')][.//div[text()='Region']]"
                )
                region_filter_chip.click()
            except Exception:
                return

        try:
            wait.until(EC.visibility_of_element_located((
                By.XPATH,
                "//input[contains(@placeholder, 'Search') or @placeholder='Search...']"
            )))
        except Exception:
            pass

        try:
            # Right panel: focus Search input (placeholder "Search...") and type region
            search_input = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//input[contains(@placeholder, 'Search') or @placeholder='Search...']"
                ))
            )
            search_input.clear()
            search_input.send_keys(region)
            time.sleep(0.5)
        except Exception:
            return

        try:
            # Select the region from the list (click element that shows the region name, e.g. "Brazil")
            region_item = wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text())='{region}']"))
            )
            region_item.click()
        except Exception:
            try:
                region_item = driver.find_element(By.XPATH, f"//*[contains(text(), '{region}')]")
                region_item.click()
            except Exception:
                pass

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

    def _wait_for_table(self, driver: webdriver.Chrome, timeout: int = 25) -> None:
        """Wait until the data table is present (e.g. div.table-container table tbody tr)."""
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.table-container table tbody tr")
            )
        )

    def _get_cell_by_testid(self, row: Tag, testid: str) -> str:
        """Get text from a td with data-testid-cell equal to testid (or containing it)."""
        cell = row.find("td", attrs={"data-testid-cell": testid})
        if not cell:
            cell = row.find("td", attrs={"data-testid-cell": lambda v: v and testid in (v or "")})
        return (cell.get_text(strip=True) or "").strip() if cell else ""

    def _extract_from_yahoo_table(self, soup: BeautifulSoup, region: str) -> list[dict]:
        """
        Extract symbol, name, price from Yahoo Finance screener table.
        Table is inside div.table-container with table.bd; cells use data-testid-cell.
        """
        rows: list[dict] = []
        container = soup.find("div", class_=lambda c: c and "table-container" in (c or ""))
        if not container:
            return rows
        table = container.find("table")
        if not table:
            return rows
        tbody = table.find("tbody")
        data_rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
        for tr in data_rows:
            symbol = self._get_cell_by_testid(tr, "ticker")
            name = self._get_cell_by_testid(tr, "companyshortname.raw")
            price = self._get_cell_by_testid(tr, "intradayprice")
            if not symbol and not name:
                continue
            region_cell = self._get_cell_by_testid(tr, "region") or ""
            region_match = not region_cell or region.lower() in region_cell.lower()
            if region_match:
                rows.append({"symbol": symbol, "name": name, "price": price})
        return rows

    def _find_column_indices(self, headers: list[str]) -> Optional[tuple[int, int, int, Optional[int]]]:
        """Return (symbol_idx, name_idx, price_idx, region_idx) or None if required columns not found."""
        headers_lower = [h.lower() for h in headers]
        symbol_idx = next((i for i, h in enumerate(headers_lower) if "symbol" in h), None)
        name_idx = next(
            (i for i, h in enumerate(headers_lower) if h == "name" or (h and "name" in h and "change" not in h and "52" not in h)),
            None,
        )
        price_idx = next(
            (i for i, h in enumerate(headers_lower) if "price" in h and "change" not in h),
            None,
        )
        region_idx = next((i for i, h in enumerate(headers_lower) if "region" in h), None)
        if symbol_idx is None or name_idx is None or price_idx is None:
            return None
        return (symbol_idx, name_idx, price_idx, region_idx)

    def _parse_price(self, price_str: str) -> float:
        """
        Converte string de preço (ex: '11,520.00') em float.
        Remove vírgulas; em caso de valor inválido retorna 0.0.
        """
        if not price_str:
            return 0.0
        try:
            return float(price_str.replace(",", ""))
        except ValueError:
            return 0.0

    def _get_table_rows(self, html: str) -> List[Tag]:
        """
        Extrai as linhas (tr) da tabela do screener no HTML.
        Procura div.screener-table, table.bd, tbody e retorna lista de tr.
        Retorna lista vazia se a estrutura não for encontrada.
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
        Extrai o total de linhas do div com classe 'total yf-c259ju'.
        O texto vem no formato '1-25 of 1067'; retorna o número após ' of ' (ex: 1067).
        Retorna 0 se não encontrar ou não conseguir fazer o parse.
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
        Extrai a quantidade de linhas por página do botão do menu (ex: 25).
        O botão tem classe menuBtn, aria-label/title com o número e um span com o texto.
        Retorna 0 se não encontrar ou não conseguir fazer o parse.
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
        Retorna True se estamos na última página da paginação (não deve clicar em Next).
        page é 0-based; total_rows é o total de itens; rows_per_page é quantos itens por página.
        """
        if rows_per_page <= 0:
            return True
        return (page + 1) * rows_per_page >= total_rows

    def click_next_page(self, driver: webdriver.Chrome, timeout: int = 10) -> None:
        """
        Clica no botão 'Next' da paginação do screener (Yahoo Finance).
        Usa data-testid='next-page-button' e aria-label='Goto next page'.
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
        # self._accept_cookies_if_present(driver)
        # self._wait_for_table(driver)

        # Clicar no botão "Region" (menuBtn) para abrir o menu/dropdown
        self._click_region_menu_button(driver)
        time.sleep(1)
        # Selecionar a região na lista de opções (div.options) e clicar em Apply
        self._select_region_from_options_and_apply(driver, region)

        # self._apply_region_filter_on_yahoo(driver, region)
        # time.sleep(2)
        # self._wait_for_table(driver)
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
