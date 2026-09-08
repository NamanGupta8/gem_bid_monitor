"""
Configuration for the GeM bid monitor.

Edit STATES to add/remove which consignee states you want to search, and
edit data/products.json to change your keyword list.
"""

from pathlib import Path

# Project root = two levels up from this file (app/config.py -> project root)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Consignee states to search (must match GeM's exact naming, e.g. "JAMMU & KASHMIR")
STATES = [
    "JAMMU & KASHMIR",
    "LADAKH"
]

PRODUCTS_FILE = DATA_DIR / "products.json"
DB_FILE = DATA_DIR / "bids.db"

# --- GeM endpoints (captured from the browser's Network tab) ---
BASE_URL = "https://bidplus.gem.gov.in"
ADVANCE_SEARCH_URL = f"{BASE_URL}/advance-search"
SEARCH_BIDS_URL = f"{BASE_URL}/search-bids"

# The CSRF form-field name GeM expects alongside the token value.
# Confirmed fixed across pagination; only the token value itself rotates
# per session, which is why we fetch it fresh at the start of every check.
CSRF_FIELD_NAME = "csrf_bd_gem_nk"

# GeM's cookie name that carries the CSRF token value
CSRF_COOKIE_NAME = "csrf_gem_cookie"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)

# Be polite: pause between paginated requests to the same host
REQUEST_DELAY_SECONDS = 1.0
