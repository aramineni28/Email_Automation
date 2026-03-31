from __future__ import annotations

import os
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

from app.H1B_Collector.cache import get_cached_sponsor, set_cached_sponsor, file_cache_lookup


def _normalize_company(company: str) -> str:
    return (company or "").strip()


def _slugify_h1bgrader(company: str) -> list[str]:
    # h1bgrader uses dash-separated slugs in many sponsor pages.
    # Keep it simple/defensive.
    return (
        company.strip()
        .lower()
        .replace("&", "and")
        .replace("/", " ")
        .replace(".", " ")
    ).split()


def _company_slug(company: str) -> str:
    parts = _slugify_h1bgrader(company)
    return "-".join(parts)


def _web_lookup_h1bgrader(company: str) -> Optional[Tuple[bool, str]]:
    """Best-effort web lookup against h1bgrader.com.

    Tries the sponsor slug page:
      https://h1bgrader.com/sponsors/<company-slug>

    Returns (True/False, source) or None if not found/undecidable.
    """
    company_q = _normalize_company(company)
    if not company_q:
        return None

    slug = _company_slug(company_q)
    url = f"https://h1bgrader.com/sponsors/{slug}"

    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None

    if r.status_code == 404:
        return None
    if r.status_code != 200 or not r.text:
        return None

    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True).lower()

    # If the page is a sponsor profile, it will usually mention H1B/LCAs.
    sponsor_words = ["h-1b", "h1b", "lca", "labor condition", "petitions", "visa"]
    negative_words = [
        "no h1b",
        "does not sponsor",
        "not sponsor",
        "no sponsorship",
        "not provide sponsorship",
    ]

    if any(w in text for w in negative_words):
        return False, f"web:h1bgrader:{url}"

    if any(w in text for w in sponsor_words):
        return True, f"web:h1bgrader:{url}"

    return None


def _web_lookup_generic(company: str) -> Optional[Tuple[bool, str]]:
    """Fallback web lookup using a URL template."""
    url_t = os.getenv("H1B_LOOKUP_URL")
    if not url_t:
        return None

    company_q = _normalize_company(company)
    if not company_q:
        return None

    url = url_t.format(company=company_q.replace(" ", "%20"))

    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None

    if r.status_code != 200 or not r.text:
        return None

    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True).lower()
    sponsor_words = ["h-1b", "h1b", "visa", "sponsor", "sponsorship"]
    negative_words = ["does not sponsor", "no sponsorship", "not sponsor"]

    if any(w in text for w in negative_words):
        return False, f"web:generic:{url}"
    if any(w in text for w in sponsor_words):
        return True, f"web:generic:{url}"

    return None


def lookup_h1b_sponsorship(company: str) -> Tuple[Optional[bool], str]:
    """Lookup H1B sponsorship with cache-first behavior.

    Order:
      1) DB cache
      2) File cache
      3) Web lookup (h1bgrader first, then optional generic template)
    """
    # 1) DB cache
    cached = get_cached_sponsor(company)
    if cached is not None:
        return cached[0], cached[1]

    # 2) File cache
    file_cached = file_cache_lookup(company)
    if file_cached is not None:
        # write-through into DB
        set_cached_sponsor(company, file_cached[0], source=file_cached[1])
        return file_cached[0], file_cached[1]

    # 3) Web
    web = _web_lookup_h1bgrader(company)
    if web is None:
        web = _web_lookup_generic(company)

    if web is not None:
        set_cached_sponsor(company, web[0], source=web[1])
        return web[0], web[1]

    return None, "unknown"
