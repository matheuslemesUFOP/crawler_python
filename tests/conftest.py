"""
Pytest fixtures shared across tests.
"""

import pytest

from crawler import Crawler


@pytest.fixture
def crawler():
    """Crawler instance with no driver (driver is None). Used for testing pure logic."""
    c = Crawler(headless=True)
    assert c._driver is None
    return c


@pytest.fixture
def html_with_table():
    """Sample HTML with screener table structure (div, table, tbody, tr)."""
    return """
    <div class="screener-table yf-hm80y7">
        <div class="total yf-c259ju">1-25 of 1067</div>
        <table class="yf-1uayyp1 bd">
            <tbody>
                <tr><td>0</td><td>AAPL</td><td>Apple Inc</td><td>x</td><td>150.25</td></tr>
                <tr><td>1</td><td>MSFT</td><td>Microsoft</td><td>x</td><td>11,520.00</td></tr>
                <tr><td>2</td><td>GOOG</td><td>Alphabet</td><td>x</td><td>140.50</td></tr>
            </tbody>
        </table>
    </div>
    """


@pytest.fixture
def html_total_only():
    """HTML with only the total div (no table)."""
    return '<div class="total yf-c259ju">1-25 of 1067</div>'


@pytest.fixture
def html_empty():
    """Empty/minimal HTML."""
    return "<html><body></body></html>"
