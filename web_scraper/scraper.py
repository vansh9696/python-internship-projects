"""
Automated ETL Web Scraping & Data Extraction Pipeline.
Extracts book catalogs, normalizes data, and produces analytical reports.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class BookScraperPipeline:
    """Robust ETL pipeline featuring retry backoff, rate-limiting, and analytics."""

    BASE_URL = "http://books.toscrape.com/catalogue/"
    START_URL = "http://books.toscrape.com/catalogue/page-1.html"

    RATING_MAP = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }

    def __init__(self, request_delay: float = 1.0, max_retries: int = 3):
        self.delay = request_delay
        self.session = self._build_resilient_session(max_retries)
        self.output_dir = Path(__file__).resolve().parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_resilient_session(self, retries: int) -> requests.Session:
        """Sets up custom headers and exponential backoff retry strategy."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        retry_strategy = Retry(
            total=retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_html(self, url: str) -> Optional[str]:
        """Performs rate-limited GET request with error handling."""
        try:
            logger.info("Fetching: %s", url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(self.delay)  # Respect rate limiting
            return response.text
        except requests.RequestException as err:
            logger.error("Failed to retrieve %s: %s", url, err)
            return None

    def parse_page(self, html: str) -> List[Dict[str, Any]]:
        """Parses individual product cards and extracts clean structured attributes."""
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("article.product_pod")
        page_records = []

        for pod in products:
            # Title & Product Link
            title_tag = pod.select_one("h3 a")
            title = title_tag.get("title", "").strip() if title_tag else "Unknown"
            rel_link = title_tag.get("href", "") if title_tag else ""
            product_url = urljoin(self.BASE_URL, rel_link)

            # Price
            price_tag = pod.select_one("p.price_color")
            price_raw = price_tag.get_text() if price_tag else "0.00"
            price_cleaned = re.sub(r"[^\d.]", "", price_raw)
            price = float(price_cleaned) if price_cleaned else 0.0

            # Stock status
            stock_tag = pod.select_one("p.instock.availability")
            in_stock = bool(stock_tag and "In stock" in stock_tag.get_text())

            # Star Rating
            rating_classes = pod.select_one("p.star-rating")
            rating = 0
            if rating_classes:
                for cls in rating_classes.get("class", []):
                    cls_lower = cls.lower()
                    if cls_lower in self.RATING_MAP:
                        rating = self.RATING_MAP[cls_lower]
                        break

            page_records.append(
                {
                    "title": title,
                    "price_gbp": price,                                                                 
                    "rating_stars": rating,
                    "in_stock": in_stock,
                    "product_url": product_url,
                }
            )

        return page_records

    def get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Locates the next pagination link if available."""
        soup = BeautifulSoup(html, "html.parser")
        next_button = soup.select_one("li.next a")
        if next_button and next_button.get("href"):
            return urljoin(current_url, next_button["href"])
        return None

    def run_pipeline(self, max_pages: int = 3) -> pd.DataFrame:
        """Executes full ETL extraction loop across specified pagination limit."""
        all_records: List[Dict[str, Any]] = []
        current_url: Optional[str] = self.START_URL
        page_count = 0

        logger.info("Starting ETL process (Limit: %d pages)...", max_pages)

        while current_url and page_count < max_pages:
            html = self.fetch_html(current_url)
            if not html:
                break

            records = self.parse_page(html)
            all_records.extend(records)
            page_count += 1

            current_url = self.get_next_page_url(html, current_url)

        df = pd.DataFrame(all_records)
        self._export_data(df)
        self.generate_analytics_report(df)
        return df

    def _export_data(self, df: pd.DataFrame) -> None:
        """Persists transformed data to CSV and JSON formats."""
        csv_path = self.output_dir / "books_extracted.csv"
        json_path = self.output_dir / "books_extracted.json"

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_json(json_path, orient="records", indent=4)

        logger.info("Saved data: %s", csv_path)
        logger.info("Saved data: %s", json_path)

    def generate_analytics_report(self, df: pd.DataFrame) -> None:
        """Computes summary statistics and exports an executive report."""
        if df.empty:
            logger.warning("No data scraped. Summary report aborted.")
            return

        total_items = len(df)
        avg_price = df["price_gbp"].mean()
        min_price = df["price_gbp"].min()
        max_price = df["price_gbp"].max()
        stock_count = df["in_stock"].sum()
        rating_dist = df["rating_stars"].value_counts().sort_index().to_dict()

        report_lines = [
            "==================================================",
            "        DATA EXTRACTION ANALYTICAL REPORT         ",
            "==================================================",
            f"Total Books Scraped       : {total_items}",
            f"In-Stock Availability     : {stock_count} ({(stock_count/total_items)*100:.1f}%)",
            f"Average Price (£)         : £{avg_price:.2f}",
            f"Cheapest Price (£)        : £{min_price:.2f}",
            f"Most Expensive Price (£)  : £{max_price:.2f}",
            "--------------------------------------------------",
            "Star Rating Breakdown (Stars : Count):",
        ]
        for stars, count in rating_dist.items():
            report_lines.append(f"  * {stars} Star{'s' if stars > 1 else ''} : {count} items")
        report_lines.append("==================================================")

        report_text = "\n".join(report_lines)
        print("\n" + report_text + "\n")

        # Save report to text file
        report_file = self.output_dir / "summary_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_text)
        logger.info("Saved statistical summary: %s", report_file)


if __name__ == "__main__":
    scraper = BookScraperPipeline(request_delay=1.0, max_retries=3)
    # Scrapes the first 3 pages (60 books total)
    scraper.run_pipeline(max_pages=3)