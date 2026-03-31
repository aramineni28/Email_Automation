import os
from datetime import datetime
from typing import Optional, Tuple

from app.models import SessionLocal, H1BSponsor


def _normalize_company(company: str) -> str:
    return (company or "").strip().lower()


def get_cached_sponsor(company: str) -> Optional[Tuple[bool, str]]:
    """Return (is_sponsor, source) if present in DB cache, else None."""
    norm = _normalize_company(company)
    if not norm:
        return None

    db = SessionLocal()
    try:
        row = db.query(H1BSponsor).filter(H1BSponsor.company == norm).first()
        if not row:
            return None
        return bool(row.is_sponsor), (row.source or "db-cache")
    finally:
        db.close()


def set_cached_sponsor(company: str, is_sponsor: bool, source: str = "web") -> None:
    norm = _normalize_company(company)
    if not norm:
        return

    db = SessionLocal()
    try:
        row = db.query(H1BSponsor).filter(H1BSponsor.company == norm).first()
        if row:
            row.is_sponsor = bool(is_sponsor)
            row.source = source
            row.checked_at = datetime.utcnow()
        else:
            db.add(
                H1BSponsor(
                    company=norm,
                    is_sponsor=bool(is_sponsor),
                    source=source,
                )
            )
        db.commit()
    finally:
        db.close()


def get_file_cache_path() -> str:
    return os.getenv("H1B_CACHE_FILE", "/app/h1b_cache.csv")


def file_cache_lookup(company: str) -> Optional[Tuple[bool, str]]:
    """Look up company in a simple CSV file cache: company,is_sponsor(0/1),source"""
    path = get_file_cache_path()
    if not os.path.exists(path):
        return None

    norm = _normalize_company(company)
    if not norm:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                c = parts[0].lower()
                if c != norm:
                    continue
                is_sponsor = parts[1] in ("1", "true", "yes", "y")
                source = parts[2] if len(parts) >= 3 else "file-cache"
                return is_sponsor, source
    except OSError:
        return None

    return None
