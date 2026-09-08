"""
Talks to GeM's bidplus.gem.gov.in search API directly (no browser needed).

Flow:
  1. GET /advance-search once -> gives us a fresh session + csrf_gem_cookie value.
  2. POST /search-bids repeatedly (incrementing "page") with that token,
     until a page comes back with no docs -> that's everything.

If GeM changes their frontend and this starts failing, the most likely
culprits are: the CSRF field name (config.CSRF_FIELD_NAME), the cookie
name the token comes from (config.CSRF_COOKIE_NAME), or the payload
shape inside search_bids_page() below. Re-capture a fresh request from
DevTools -> Network -> search-bids -> Payload tab and compare.
"""

import json
import time
import logging
from typing import List, Dict

import requests

from app import config

log = logging.getLogger(__name__)


class GemSearchError(Exception):
    pass


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": config.USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": config.ADVANCE_SEARCH_URL,
            "Origin": config.BASE_URL,
        }
    )
    return session


def get_csrf_token(session: requests.Session) -> str:
    """Hit /advance-search once to obtain a fresh CSRF token via cookies."""
    resp = session.get(config.ADVANCE_SEARCH_URL, timeout=20)
    resp.raise_for_status()

    token = session.cookies.get(config.CSRF_COOKIE_NAME)
    if not token:
        raise GemSearchError(
            f"Could not find '{config.CSRF_COOKIE_NAME}' cookie after GET "
            f"{config.ADVANCE_SEARCH_URL}. GeM may have changed their CSRF setup — "
            "re-check DevTools for the current cookie name."
        )
    return token


def search_bids_page(
    session: requests.Session, csrf_token: str, state_name: str, page: int
) -> dict:
    """Fetch a single page of results for a given consignee state."""
    payload = {
        "searchType": "con",
        "state_name_con": state_name,
        "city_name_con": "",
        "bidEndFromCon": "",
        "bidEndToCon": "",
        "page": page,
    }

    form_data = {
        "payload": json.dumps(payload),
        config.CSRF_FIELD_NAME: csrf_token,
    }

    resp = session.post(
        config.SEARCH_BIDS_URL,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        timeout=20,
    )
    resp.raise_for_status()

    try:
        return resp.json()
    except ValueError as exc:
        raise GemSearchError(
            f"search-bids did not return JSON (page {page}, state {state_name}). "
            f"Got: {resp.text[:300]!r}"
        ) from exc


def _normalize_doc(doc: dict) -> Dict:
    """Pull out the fields we actually care about from a raw 'docs' entry."""

    def first(field, default=""):
        val = doc.get(field, default)
        if isinstance(val, list):
            return val[0] if val else default
        return val

    return {
        "bid_no": first("b_bid_number"),
        "bid_id": str(first("b_id")),
        "items": first("b_category_name"),
        "quantity": str(first("b_total_quantity")),
        "start_date": first("final_start_date_sort"),
        "end_date": first("final_end_date_sort"),
        "ministry": first("ba_official_details_minName"),
        "department": first("ba_official_details_deptName"),
    }


def fetch_all_bids_for_state(state_name: str) -> List[Dict]:
    """Loop through pagination until GeM returns no more docs."""
    session = _new_session()
    csrf_token = get_csrf_token(session)
    log.info("Got CSRF token for state=%s", state_name)

    all_bids: List[Dict] = []
    page = 1
    while True:
        data = search_bids_page(session, csrf_token, state_name, page)

        response = data.get("response", {}).get("response", {})
        docs = response.get("docs", [])
        num_found = response.get("numFound", 0)

        if not docs:
            break

        all_bids.extend(_normalize_doc(d) for d in docs)
        log.info(
            "state=%s page=%d -> %d docs (running total %d/%d)",
            state_name, page, len(docs), len(all_bids), num_found,
        )

        if len(all_bids) >= num_found:
            break

        page += 1
        time.sleep(config.REQUEST_DELAY_SECONDS)

    return all_bids


def fetch_all_bids() -> List[Dict]:
    """Fetch bids across every state configured in config.STATES."""
    results: List[Dict] = []
    for state in config.STATES:
        try:
            results.extend(fetch_all_bids_for_state(state))
        except (requests.RequestException, GemSearchError) as exc:
            log.error("Failed fetching state=%s: %s", state, exc)
    return results
