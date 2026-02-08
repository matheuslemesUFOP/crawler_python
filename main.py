"""
Main entry point: runs the crawler using URL and region from configuration.

Configuration is read from environment variables (e.g. via .env file).
See .env.example for required variables.
"""

import logging
import os
import sys

from dotenv import load_dotenv

from crawler import Crawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Application:
    """Orchestrates configuration loading and crawler execution."""

    def __init__(self) -> None:
        """Load configuration from environment (no hardcoded values)."""
        self._url: str = ""
        self._region: str = "Brazil"
        self._output_path: str = f"output_{self._region}.csv"
        self._load_config()

    def _load_config(self) -> None:
        """Read URL, region and output path from environment; exit if URL is missing."""
        load_dotenv()

        url = os.environ.get("CRAWLER_URL")
        if not url or not url.strip():
            print(
                "Error: CRAWLER_URL is not set. Create a .env file from .env.example or set the variable.",
                file=sys.stderr,
            )
            sys.exit(1)

        self._url = url.strip()
        self._region = (os.environ.get("CRAWLER_REGION", "Brazil") or "Brazil").strip()
        self._output_path = (os.environ.get("CRAWLER_OUTPUT", f"output_{self._region}.csv") or f"output_{self._region}.csv").strip()

    def run(self) -> None:
        """Run the crawler and export results to CSV."""
        logger = logging.getLogger(__name__)
        logger.info("Starting crawler for region=%s, output=%s", self._region, self._output_path)
        with Crawler(headless=True) as crawler:
            df = crawler.extract(self._url, self._region)
            path = crawler.export_csv(df, self._output_path)
            print(f"Extracted {len(df)} record(s). Exported to: {path}")


def main() -> None:
    """Entry point: create application and run."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
