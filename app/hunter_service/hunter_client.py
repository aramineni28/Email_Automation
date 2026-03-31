import requests
import os
from app.config import HUNTER_API_KEY


def search_recruiters(domain):
    api_key = HUNTER_API_KEY

    if not api_key:
        raise ValueError("HUNTER_API_KEY environment variable not set")

    url = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": api_key,
        "limit": 10  # Free tier limit is 10 emails
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Check for errors
    if "errors" in data and data["errors"]:
        print(f"Hunter.io Error: {data['errors']}")
        return {"people": []}

    # Transform Hunter.io response to match expected format
    if data.get("data") and data["data"].get("emails"):
        people = []
        for email in data["data"]["emails"]:
            first = email.get("first_name") or ""
            last = email.get("last_name") or ""
            name = (first + " " + last).strip() or None
            people.append(
                {
                    "name": name,
                    "email": email.get("value"),
                    "title": email.get("position") or "Unknown",
                }
            )

        return {"people": people}

    return {"people": []}