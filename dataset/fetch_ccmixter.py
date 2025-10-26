"""
A script to fetch music metadata from ccMixter (https://ccmixter.org/query-api).
It only retrieves uploads licensed under Creative Commons Attribution license (CC BY).
The script is intended to make the music selection process easier.
Only a small subset of the files will be included in the dataset.
"""

import json
import time
import http.client
import urllib.parse
import ssl
import re
from pathlib import Path


BASE_URL = "https://ccmixter.org/api/query"
LIMIT = 100
SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "ccmixter_data.jsonl"

http.client._MAXLINE = 1048576


def fix_invalid_json(text):
    text = re.sub(r':\s*0+(\d+)', r': \1', text)
    return text


def fetch_page(offset=0):
    params = urllib.parse.urlencode({
        "limit": LIMIT,
        "lic": "by",
        "f": "json",
        "offset": offset
    })

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    conn = http.client.HTTPSConnection("ccmixter.org", context=ctx)
    conn.request("GET", f"/api/query?{params}")

    response = conn.getresponse()
    content = response.read()
    conn.close()

    for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
        try:
            decoded = content.decode(encoding)
            try:
                return json.loads(decoded)
            except json.JSONDecodeError:
                fixed = fix_invalid_json(decoded)
                return json.loads(fixed)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    return None


def main():
    offset = 0
    all_items = []

    with open(OUTPUT_FILE, "w") as f:
        while True:
            print(f"Fetching page at offset {offset}...")
            data = fetch_page(offset)

            if data is None:
                print(f"Skipping page at offset {offset} due to encoding/parsing errors")
                offset += LIMIT
                time.sleep(1)
                continue

            if not data:
                break

            for item in data:
                f.write(json.dumps(item) + "\n")

            all_items.extend(data)

            if len(data) < LIMIT:
                break

            offset += LIMIT
            time.sleep(1)

    print(f"Fetched {len(all_items)} items total")
    print(f"Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
