def extract_recruiter_emails(domain_or_url):
    from urllib.parse import urlparse
    from app.hunter_service.hunter_client import search_recruiters
    import os

    # If it looks like a URL, extract the domain; otherwise use it as-is
    if "://" in domain_or_url:
        parsed_url = urlparse(domain_or_url)
        domain = parsed_url.netloc
    else:
        domain = domain_or_url

    data = search_recruiters(domain)
    print(f"Hunter.io API response for {domain}: {data}")  # Debug line

    # --- Title-based filtering ---
    # You can control filtering via env vars:
    #   TITLE_FILTER_PRESET=recruiter_only|recruiter_hr|recruiter_hr_managers
    #   TITLE_KEYWORDS_INCLUDE=comma,separated,keywords  (overrides preset include list)
    #   TITLE_KEYWORDS_EXCLUDE=comma,separated,keywords  (optional)

    preset = (os.getenv("TITLE_FILTER_PRESET") or "recruiter_hr_managers").strip().lower()

    include_presets = {
        "recruiter_only": [
            "recruit", "sourc", "talent acquisition", "talent", "staffing",
        ],
        "recruiter_hr": [
            "recruit", "sourc", "talent acquisition", "talent", "staffing",
            "human resources", "hr", "people operations", "people ops", "people partner",
        ],
        "recruiter_hr_managers": [
            # Recruiters / HR
            "recruit", "sourc", "talent acquisition", "talent", "staffing",
            "human resources", "hr", "people operations", "people ops", "people partner",
            # Hiring managers / technical leadership (kept reasonably specific)
            "hiring manager",
            "engineering manager",
            "software engineering manager",
            "technical manager",
            "tech lead",
            "team lead",
            "head of engineering",
            "director of engineering",
            "vp engineering",
            "cto",
            "platform",
            "infrastructure",
            "site reliability",
            "sre",
            "devops",
        ],
    }

    default_include = include_presets.get(preset, include_presets["recruiter_hr_managers"])

    env_include = os.getenv("TITLE_KEYWORDS_INCLUDE")
    include_keywords = (
        [k.strip().lower() for k in env_include.split(",") if k.strip()]
        if env_include
        else [k.lower() for k in default_include]
    )

    env_exclude = os.getenv("TITLE_KEYWORDS_EXCLUDE")
    exclude_keywords = (
        [k.strip().lower() for k in env_exclude.split(",") if k.strip()]
        if env_exclude
        else [
            # Reduce obvious non-target roles if you use broad include terms
            "sales",
            "marketing",
            "business development",
            "partnership",
            "account",
            "finance",
            "compensation",
        ]
    )

    recruiters = []
    for person in data.get("people", []):
        title = (person.get("title") or "").strip()
        title_l = title.lower()

        # If Hunter doesn't return a title, skip by default
        if not title_l:
            continue

        if any(x in title_l for x in exclude_keywords):
            continue

        if any(k in title_l for k in include_keywords):
            recruiters.append({
                "name": person.get("name"),
                "email": person.get("email"),
                "title": title
            })

    return recruiters

def extract_all_emails(domain_or_url):
    """Return all discovered emails for a domain/URL (no title filtering).

    This is useful for saving everything into the DB, while using
    `extract_recruiter_emails` for deciding who should be emailed.
    """
    from urllib.parse import urlparse
    from app.hunter_service.hunter_client import search_recruiters

    if "://" in domain_or_url:
        parsed_url = urlparse(domain_or_url)
        domain = parsed_url.netloc
    else:
        domain = domain_or_url

    data = search_recruiters(domain)
    people = []
    for person in data.get("people", []):
        people.append(
            {
                "name": person.get("name"),
                "email": person.get("email"),
                "title": (person.get("title") or "").strip() or None,
            }
        )
    return people