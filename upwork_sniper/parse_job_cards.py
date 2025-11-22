"""Helper utilities to normalize job payloads returned by Upwork search APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _safe_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            return [item.get("name") or item.get("skill", "") for item in value if isinstance(item, dict)]
        return [str(item) for item in value]
    return [str(value)]


def _parse_budget(job: Dict[str, Any]) -> Dict[str, Any]:
    budget = job.get("budget") or job.get("amount", {})
    if isinstance(budget, dict):
        return {
            "type": budget.get("type") or job.get("type"),
            "budget": budget.get("budget") or budget.get("amount"),
            "currency": budget.get("currency") or budget.get("currency_code"),
        }

    if budget:
        return {"type": job.get("type"), "budget": budget, "currency": job.get("currency")}

    hourly = job.get("hourly") or {}
    if isinstance(hourly, dict):
        return {
            "type": "hourly",
            "hourly_min": hourly.get("min_rate") or hourly.get("min"),
            "hourly_max": hourly.get("max_rate") or hourly.get("max"),
            "currency": hourly.get("currency"),
        }

    hourly_rate = {
        "type": "hourly",
        "hourly_min": job.get("hourly_rate_min"),
        "hourly_max": job.get("hourly_rate_max"),
        "currency": job.get("currency") or job.get("hourly_currency"),
    }
    if hourly_rate["hourly_min"] or hourly_rate["hourly_max"]:
        return hourly_rate

    return {}


def _parse_posted_time(job: Dict[str, Any]) -> str:
    timestamp = (
        job.get("publish_time")
        or job.get("published_time")
        or job.get("created_on")
        or job.get("date_created")
        or job.get("posted_on")
    )
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp / 1000 if timestamp > 10**12 else timestamp, tz=timezone.utc).isoformat()
    if isinstance(timestamp, str):
        return timestamp
    return ""


def extract_jobs_from_payload(payload: Dict[str, Any], keyword: str) -> List[Dict[str, Any]]:
    """
    Normalize the search payload coming from Upwork endpoints into a clean list of dicts.
    """
    jobs: List[Dict[str, Any]] = []
    if not payload:
        return jobs

    buckets: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list):
            buckets = payload["results"]
        elif "jobs" in payload and isinstance(payload["jobs"], list):
            buckets = payload["jobs"]
        elif "searchResults" in payload and isinstance(payload["searchResults"], dict):
            jobs_block = payload["searchResults"].get("jobs", {})
            buckets = jobs_block.get("results", [])

    for entry in buckets:
        job_id = entry.get("ciphertext") or entry.get("job_id") or entry.get("id") or entry.get("oid")
        if not job_id:
            continue

        client = entry.get("client") or {}

        normalized = {
            "job_id": str(job_id),
            "keyword": keyword,
            "title": entry.get("title", ""),
            "description": entry.get("snippet") or entry.get("description", ""),
            "skills": _safe_list(entry.get("skills")),
            "posted_time": _parse_posted_time(entry),
            "category": entry.get("category2") or entry.get("subcategory2") or entry.get("category"),
            "budget": _parse_budget(entry),
            "client": {
                "payment_verified": client.get("payment_verification_status") or client.get("payment_verified"),
                "past_hires": client.get("past_hires") or client.get("total_posted_jobs"),
                "country": client.get("location") or client.get("country"),
            },
            "proposals": entry.get("proposals") or entry.get("num_proposals"),
            "connects_needed": entry.get("connects") or entry.get("connects_required"),
            "url": entry.get("url") or entry.get("link"),
        }

        jobs.append(normalized)

    return jobs


