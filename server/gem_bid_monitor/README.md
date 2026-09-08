# GeM Bid Monitor

Fetches ongoing GeM (Government e-Marketplace) bids for configured consignee
states, matches them against your keyword list, and surfaces new matches
(bid number + items + department + end date) via a local FastAPI service.

Talks directly to GeM's `search-bids` JSON API (reverse-engineered from the
browser's Network tab) — no HTML scraping, no browser automation needed.

## Setup

```bash
pip install -r requirements.txt
```

Edit `data/products.json` with your real product keywords:

```json
{
  "keywords": ["defibrillator", "hard disk drive", "your product here"]
}
```

Edit `app/config.py` if you want to search more/different states — see
the `STATES` list.

## Run

```bash
uvicorn app.main:app --reload
```

On startup, it immediately fetches + matches bids and logs results to the
terminal. It also exposes:

- `GET /matches` — every match found so far (persisted in `data/bids.db`,
  survives restarts)
- `POST /check-now` — re-run the fetch + match on demand, without restarting

## Project structure

```
gem_bid_monitor/
├── app/
│   ├── main.py             # FastAPI app + routes
│   ├── config.py           # states to search, file paths, GeM endpoints
│   ├── schemas.py          # Pydantic response models
│   └── core/
│       ├── scraper.py      # GeM API client (CSRF handshake + pagination)
│       ├── matcher.py      # keyword matching against products.json
│       └── store.py        # SQLite persistence of matched bids
├── data/
│   └── products.json       # your editable keyword list
├── requirements.txt
└── .gitignore
```

## If it stops working

GeM's `search-bids` endpoint needs a CSRF token grabbed from a prior GET to
`/advance-search`. If GeM changes their frontend, the most likely breakage
points are in `app/config.py`:

- `CSRF_COOKIE_NAME` — the cookie the token comes from
- `CSRF_FIELD_NAME` — the form field name the token must also be sent as

Re-check these via browser DevTools → Network tab → the `search-bids`
request → Headers (for the cookie) and Payload (for the field name).
