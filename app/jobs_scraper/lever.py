import requests


def fetch_lever_jobs(company):
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"

    response = requests.get(url)

    if response.status_code != 200:
        return []

    jobs = response.json()

    target = []

    keywords = [
        "site reliability",
        "devops",
        "cloud",
        "infrastructure",
        "network",
        "SRE",
        "reliability",
        "operations",
        "platform",
        "systems"
    ]

    for job in jobs:
        title = job["text"].lower()

        if any(k in title for k in keywords):
            target.append({
                "title": job["text"],
                "link": job["hostedUrl"]
            })

    return target