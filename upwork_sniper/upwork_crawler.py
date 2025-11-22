"""Playwright-based Upwork crawler using stored cookies and search keywords."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote

from playwright.async_api import (
    PlaywrightTimeoutError,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from . import BASE_DIR, load_config
from .parse_job_cards import extract_jobs_from_payload


class UpworkCrawler:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.browser_conf = config.get("browser", {})
        self.search_conf = config.get("search", {})
        self.output_conf = config.get("output", {})
        self.logger = logging.getLogger("UpworkCrawler")
        self.logger.setLevel(getattr(logging, config.get("logging", {}).get("level", "INFO")))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))
            self.logger.addHandler(handler)

        self.cookies_path = Path(self.browser_conf.get("cookies_path", "upwork_sniper/cookies.json"))
        if not self.cookies_path.is_absolute():
            self.cookies_path = BASE_DIR / self.cookies_path.name

        self.interval_seconds = self.search_conf.get("interval_seconds", 45)
        self.retry_attempts = self.browser_conf.get("retry_attempts", 3)
        self.backoff_seconds = self.browser_conf.get("backoff_seconds", 20)
        self.seen_ids: set[str] = set()

    async def _ensure_cookies_exist(self) -> None:
        if not self.cookies_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy cookies tại {self.cookies_path}. Chạy `python -m upwork_sniper.login_once` trước."
            )

    def _build_query_url(self, keyword: str, page: int) -> str:
        paging = f"{page * self.search_conf.get('per_page', 50)}%3B{self.search_conf.get('per_page', 50)}"
        params = {
            "sort": self.search_conf.get("sort", "recency"),
            "paging": paging,
            "per_page": self.search_conf.get("per_page", 50),
            "q": keyword,
        }
        base_api = self.search_conf.get("api_url", "https://www.upwork.com/ab/jobs/search/api")
        return f"{base_api}?{urlencode(params)}"

    async def _fetch_keyword(self, context, keyword: str) -> List[Dict[str, Any]]:
        jobs: List[Dict[str, Any]] = []
        max_pages = self.search_conf.get("max_pages", 1)

        for page in range(max_pages):
            url = self._build_query_url(keyword, page)
            for attempt in range(1, self.retry_attempts + 1):
                response = await context.request.get(
                    url,
                    headers={
                        "User-Agent": self.browser_conf.get("user_agent"),
                        "Accept": "application/json,text/plain,*/*",
                        "Referer": self.search_conf.get("page_url"),
                    },
                )
                status = response.status
                if status == 429:
                    self.logger.warning("429 detected for '%s' (page %s). Retry %s/%s", keyword, page + 1, attempt, self.retry_attempts)
                    await asyncio.sleep(self.backoff_seconds * attempt)
                    continue
                if status >= 400:
                    self.logger.error("HTTP %s for '%s' page %s: %s", status, keyword, page + 1, await response.text())
                    await asyncio.sleep(self.backoff_seconds)
                    continue

                payload = await response.json()
                page_jobs = extract_jobs_from_payload(payload, keyword)
                self.logger.info("Keyword '%s' page %s → %s jobs", keyword, page + 1, len(page_jobs))
                jobs.extend(page_jobs)
                break
            else:
                self.logger.error("Bó tay keyword '%s' page %s sau %s lần retry", keyword, page + 1, self.retry_attempts)

        return jobs

    async def run_once(self) -> List[Dict[str, Any]]:
        await self._ensure_cookies_exist()
        storage_state = json.loads(self.cookies_path.read_text(encoding="utf-8"))

        keywords = self.search_conf.get("keywords") or []
        if not keywords:
            self.logger.warning("Không có keyword nào trong config. Dừng crawler.")
            return []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.browser_conf.get("headless", False),
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                storage_state=storage_state,
                user_agent=self.browser_conf.get("user_agent"),
                viewport={"width": 1400, "height": 900},
                timeout=self.browser_conf.get("timeout_ms", 25000),
            )

            page = await context.new_page()
            await page.goto(self.search_conf.get("page_url"), wait_until="domcontentloaded")

            all_jobs: List[Dict[str, Any]] = []
            for keyword in keywords:
                try:
                    jobs = await self._fetch_keyword(context, keyword)
                    all_jobs.extend(jobs)
                except PlaywrightTimeoutError:
                    self.logger.error("Timeout lúc crawl keyword '%s'", keyword)

            await browser.close()
            return self._dedupe_jobs(all_jobs)

    def _dedupe_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped = []
        for job in jobs:
            job_id = job.get("job_id")
            if not job_id or job_id in self.seen_ids:
                continue
            self.seen_ids.add(job_id)
            deduped.append(job)
        return deduped

    def persist(self, jobs: List[Dict[str, Any]]) -> Optional[Path]:
        if not jobs:
            self.logger.info("Không có job mới để lưu.")
            return None

        output_path = Path(self.output_conf.get("path", "data/upwork_jobs.jsonl"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("a", encoding="utf-8") as f:
            for job in jobs:
                f.write(json.dumps(job, ensure_ascii=False) + "\n")

        self.logger.info("Đã lưu %s job mới vào %s", len(jobs), output_path)
        return output_path


async def main():
    config = load_config()
    crawler = UpworkCrawler(config)
    jobs = await crawler.run_once()
    crawler.persist(jobs)


if __name__ == "__main__":
    asyncio.run(main())


