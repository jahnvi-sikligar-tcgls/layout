# =========================
# Fixed scraper (safe version)
# =========================

import os
import re
import time
import random
from networkx import display
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# -------- Config --------
SEARCH_URLS = [
    "https://housing.com/in/buy/projects/page/311218-merlin-ventana-by-merlin-in-baner",
    #"https://housing.com/in/buy/searches/P2q1uwqz5uo79lvmy",
    # add more...
]
CSV_PATH = "my_csv.csv"
BASE_URL = "https://housing.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# -------- Helpers --------

def fetch_html(url, timeout=25):
    """
    Returns (ok, html_text, reason)
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        return False, "", f"request_error: {e}"

    if resp.status_code != 200:
        return False, "", f"http_{resp.status_code}"

    html = resp.text
    low = html.lower()

    # anti-bot / block detection
    block_signals = [
        "request blocked",
        "security alert",
        "temporarily blocked",
        "suspicious activity",
        "captcha",
        "access denied",
    ]
    if any(sig in low for sig in block_signals):
        return False, html, "blocked_by_site"

    return True, html, "ok"


def extract_listing_urls_from_search(search_url):
    """
    Try multiple link patterns instead of one strict pattern.
    """
    ok, html, reason = fetch_html(search_url)
    if not ok:
        print(f"[WARN] {search_url} -> {reason}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    # collect all hrefs
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(BASE_URL, href)

        # broad patterns for listing pages (adjust as needed)
        if re.search(r"/in/buy/(projects|project|apartment|flats|resale|property)/", full):
            urls.add(full)

        # your original pattern kept as fallback
        if "/in/buy/projects/page/" in full:
            urls.add(full)

    # fallback regex from raw HTML
    if not urls:
        matches = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
        for href in matches:
            full = urljoin(BASE_URL, href)
            if re.search(r"/in/buy/", full):
                urls.add(full)

    return sorted(urls)


def extract_data(listing_url):
    """
    Safer extraction with checks so it doesn't crash on missing nodes.
    """
    ok, html, reason = fetch_html(listing_url)
    if not ok:
        print(f"[WARN] listing skipped {listing_url} -> {reason}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    result = {"source_url": listing_url}

    # title / flat type
    h1 = soup.find("h1")
    result["title"] = h1.get_text(" ", strip=True) if h1 else ""

    # price-ish text (best effort)
    price_node = soup.find(string=re.compile(r"₹|rs\.?", re.I))
    result["price_text"] = price_node.strip() if isinstance(price_node, str) else ""

    # collect visible key-value-ish table rows
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if len(cells) >= 2:
                k = cells[0].get_text(" ", strip=True)
                v = cells[1].get_text(" ", strip=True)
                if k and v:
                    result[k] = v

    # about text (best effort)
    about = soup.find("div", class_=re.compile(r"about", re.I))
    if about:
        result["about"] = about.get_text(" ", strip=True)

    return pd.DataFrame([result])


def append_to_csv(df, path=CSV_PATH):
    """
    Append safely. Create file if missing.
    """
    if df is None or df.empty:
        return

    if os.path.exists(path):
        old = pd.read_csv(path)
        merged = pd.concat([old, df], ignore_index=True)
        merged.drop_duplicates(subset=["source_url"], inplace=True)
        merged.to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)


# -------- Main run --------

total_links = 0
total_rows = 0

for search_url in SEARCH_URLS:
    print(f"\n[INFO] Search URL: {search_url}")
    listing_urls = extract_listing_urls_from_search(search_url)
    print(f"[INFO] Found listing links: {len(listing_urls)}")

    total_links += len(listing_urls)

    for listing_url in listing_urls:
        try:
            df = extract_data(listing_url)
            if df is not None and not df.empty:
                append_to_csv(df, CSV_PATH)
                total_rows += len(df)
        except Exception as e:
            print(f"[ERROR] Failed on {listing_url}: {e}")

        # polite delay
        time.sleep(random.uniform(1.2, 2.4))

# Final safe read
if os.path.exists(CSV_PATH):
    out = pd.read_csv(CSV_PATH)
    print(f"\n[DONE] CSV rows: {len(out)} | path: {CSV_PATH}")
    display(out.head())
else:
    print("\n[DONE] No CSV created. Likely blocked or no matching listing links found.")
