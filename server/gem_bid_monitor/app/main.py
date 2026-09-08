"""
Run with:  uvicorn app.main:app --reload   (from the project root)

- On startup: fetches bids for every state in config.STATES, matches them
  against data/products.json, saves new matches to SQLite, logs a summary.
- GET  /matches     -> everything found so far (persists across restarts)
- POST /check-now   -> re-runs the fetch+match without restarting the server
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import scraper, matcher, store
from app.schemas import CheckResult, MatchesResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="GeM Bid Monitor")

# Allow the Angular dev server (localhost:4200) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    return {
        "bids_fetched": len(bids),
        "total_matches": len(matches),
        "new_matches": new_matches,
    }


@app.on_event("startup")
def on_startup():
    store.init_db()
    # run_check()


@app.post("/check-now", response_model=CheckResult)
def check_now():
    return run_check()


@app.get("/matches", response_model=MatchesResponse)
def get_matches():
    return {"matches": store.all_matches()}


@app.get("/")
def root():
    return {"status": "running", "endpoints": ["/matches", "/check-now (POST)"]}
