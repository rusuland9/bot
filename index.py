#!/usr/bin/env python3
"""
slack_people_from_env.py
Reads SLACK_COOKIE and SLACK_XOXC from .env and sends the same
POST request to the Slack internal endpoint you captured.

Produces:
 - slack_people_response.json  (if JSON returned)
 - slack_people_raw.txt       (if non-JSON text returned)
 - slack_people_response.html (if HTML returned, e.g. login)
"""

import os
import json
import sys
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment

# Ensure stdout can print Unicode symbols (e.g., checkmarks, warning signs) on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COOKIE = os.getenv("SLACK_COOKIE", "").strip()
XOXC_TOKEN = os.getenv("SLACK_XOXC", "").strip()

if not COOKIE or not XOXC_TOKEN:
    print("ERROR: please set SLACK_COOKIE and SLACK_XOXC in your .env file")
    sys.exit(1)

REQUEST_URL = (
    "https://shopifypartners.slack.com/api/search.modules.people"
    "?_x_id=58298780-1759773573.777"
    "&slack_route=T4BB7S7HP"
    "&_x_version_ts=1759765056"
    "&_x_frontend_build_type=current"
    "&_x_desktop_ia=4"
    "&_x_gantry=true"
    "&fp=e3"
    "&_x_num_retries=0"
)

FORM_FIELDS = {
    "module": "people",
    "query": "",
    "page": "1",
    "client_req_id": "b41b784c-0337-4b54-9e30-6d0529a62ea2",
    "browse_session_id": "7e96d9ba-cb08-40dc-b4a1-413c282476b9",
    "extracts": "0",
    "highlight": "0",
    "extra_message_data": "1",
    "no_user_profile": "1",
    "count": "50",
    "file_title_only": "false",
    "query_rewrite_disabled": "false",
    "include_files_shares": "1",
    "browse": "standard",
    "search_context": "desktop_people_browser",
    "max_filter_suggestions": "10",
    "sort": "name",
    "sort_dir": "asc",
    "hide_deactivated_users": "1",
    "custom_fields": "{}",
    "_x_reason": "browser-query",
    "_x_mode": "online",
    "_x_sonic": "true",
    "_x_app_name": "client",
}

def build_session_from_cookie(cookie_header: str) -> requests.Session:
    s = requests.Session()
    # parse the cookie string into name/value pairs and set in session cookiejar
    pairs = [p.strip() for p in cookie_header.split(";") if p.strip()]
    for p in pairs:
        if "=" in p:
            name, value = p.split("=", 1)
            # set cookie for the slack domain
            s.cookies.set(name.strip(), value.strip(), domain="shopifypartners.slack.com")
    return s

def main():
    s = build_session_from_cookie(COOKIE)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ja,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7,zh;q=0.6,id;q=0.5,de;q=0.4",
        "Origin": "https://app.slack.com",
        "Referer": "https://app.slack.com/client/T4BB7S7HP/people",
        # client-hint headers (optional)
        "Sec-CH-UA": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Sec-CH-UA-Platform": '"Windows"',
    }

    # build multipart fields. Using requests `files` with (None, value) sends form-data
    files = {k: (None, v) for k, v in FORM_FIELDS.items()}
    files["token"] = (None, XOXC_TOKEN)

    print("Sending request...")
    resp = s.post(REQUEST_URL, headers=headers, files=files, timeout=30, allow_redirects=True)

    print("HTTP", resp.status_code)
    ct = resp.headers.get("Content-Type", "")

    text = resp.text

    # detect HTML/login
    if "text/html" in ct or "<!doctype html" in text.lower() or "login" in resp.url.lower():
        print("⚠️ Received HTML (login page or redirect). Your cookie/token may be invalid.")
        with open("slack_people_response.html", "w", encoding="utf-8") as f:
            f.write(text)
        print("Saved slack_people_response.html for inspection.")
        return

    # try parse JSON
    try:
        j = resp.json()
    except ValueError:
        print("⚠️ Response not JSON. Saving raw text.")
        with open("slack_people_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Saved slack_people_raw.txt")
        return

    with open("slack_people_response.json", "w", encoding="utf-8") as f:
        json.dump(j, f, indent=2, ensure_ascii=False)

    print("✅ Saved slack_people_response.json")
    # print a small summary
    if isinstance(j, dict) and "items" in j:
        print("Items returned:", len(j["items"]))
    else:
        print("Top-level JSON keys:", list(j.keys()) if isinstance(j, dict) else "non-dict")

if __name__ == "__main__":
    main()
