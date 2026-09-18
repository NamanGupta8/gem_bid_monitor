"""
Run with:  uvicorn app.main:app --host 0.0.0.0 --reload   (from the project root)

- On startup: just prepares the SQLite DB — the server is ready instantly.
- GET  /matches     -> everything found so far (persists across restarts)
- POST /check-now   -> fetches bids from GeM, matches against
  data/products.json, saves new matches, and returns the result. This is
  the ONLY thing that triggers a live GeM fetch — nothing runs automatically,
  and nothing blocks the server from starting.

--host 0.0.0.0 makes this reachable from other devices on your network at
http://<your-lan-ip>:8000 — not just from this machine via localhost.
"""

import logging
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core import scraper, matcher, store
from app.schemas import CheckResult, MatchesResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="GeM Bid Monitor")

# Allow the Angular dev server whether it's opened via localhost or via this
# machine's LAN IP (e.g. http://192.168.1.23:4200) — any host, port 4200.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):4200",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only one check should ever run at a time — this matters once multiple
# laptops share one backend, since two concurrent GeM scrapes would be
# wasteful and could hit SQLite with simultaneous writes ("database is
# locked" errors). A second laptop's request while one is already running
# gets a clear 409 instead of silently racing it.
_check_lock = threading.Lock()


def run_check() -> dict:
    log.info("Starting bid check...")
    bids = scraper.fetch_all_bids()
    log.info("Fetched %d bids total.", len(bids))

    matches = matcher.find_matches(bids)
    log.info("%d bids matched your keywords.", len(matches))

    new_matches = store.save_matches(matches)
    log.info("%d of those are new (not seen in a previous check).", len(new_matches))

    for m in new_matches:
        log.info(
            "NEW MATCH: %s | %s | matched on: %s",
            m["bid_no"], m["items"][:80], m["matched_keywords"],
        )

    # Anything previously matched but absent from this fresh set of matches
    # is no longer live/relevant on GeM (closed, cancelled, or corrigendum'd
    # off the list) — stop showing it without losing the historical record.
    deactivated = store.deactivate_stale(m["bid_no"] for m in matches)
    if deactivated:
        log.info("%d bid(s) no longer available, removed from view: %s", len(deactivated), deactivated)

    return {
        "bids_fetched": len(bids),
        "total_matches": len(matches),
        "new_matches": new_matches,
    }


@app.on_event("startup")
def on_startup():
    # Just prep the DB — no automatic GeM fetch on startup. The server (and
    # the UI) are ready instantly, with whatever's already in SQLite from
    # last time. "Check now" is the only thing that triggers a live fetch.
    store.init_db()


@app.post("/check-now", response_model=CheckResult)
def check_now():
    # Non-blocking: if someone else's check is already running, fail fast
    # with a clear message instead of queuing this laptop's request for
    # several minutes behind it (which would look like a hang).
    if not _check_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="A check is already in progress (started from another device). Try again shortly.",
        )
    try:
        return run_check()
    finally:
        _check_lock.release()


@app.get("/matches", response_model=MatchesResponse)
def get_matches():
    return {"matches": store.all_matches()}


@app.get("/")
def root():
    return {"status": "running", "endpoints": ["/matches", "/check-now (POST)"]}