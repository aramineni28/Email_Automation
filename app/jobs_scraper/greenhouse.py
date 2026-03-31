import requests


def fetch_greenhouse_jobs(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

    response = requests.get(url)

    if response.status_code != 200:
        return []

    jobs = response.json().get("jobs", [])

    target = []

    keywords = [
        "site reliability",
        "devops",
        "cloud",
        "infrastructure",
        "network"
    ]

    for job in jobs:
        title = job["title"].lower()

        if any(k in title for k in keywords):
            target.append({
                "title": job["title"],
                "link": job["absolute_url"]
            })

    return target