# GeM Bid Monitor

Automatically finds live bids on [GeM](https://gem.gov.in) (Government e-Marketplace)
that match your products, so you don't have to click through hundreds of pages
by hand.

## What this project does

GeM publishes thousands of ongoing bids, filterable by consignee state, but
there's no way to filter them by *your* products — you have to scroll through
everything and check manually. This project automates that:

1. **Backend (FastAPI + Python)** — talks directly to GeM's own search API
   (`bidplus.gem.gov.in/search-bids`), pages through every bid for your
   configured state(s), and checks each one's items against a keyword list
   you control.
2. **Frontend (Angular + Tailwind)** — a local dashboard showing every match
   in a filterable, paginated table. Clicking a bid number opens the real
   bid on GeM in a new tab.

Nothing runs automatically in the background — you press **Check now**, it
fetches fresh data from GeM (can take a few minutes, since GeM pages results
~10 at a time), and matches get saved locally so they persist across restarts.

## Project structure

```
gem-bid-monitor/
├── backend/            # FastAPI service — talks to GeM, matches keywords
│   ├── app/
│   │   ├── main.py         # API routes: /matches, /check-now
│   │   ├── config.py       # states to search, file paths
│   │   ├── schemas.py      # API response shapes
│   │   └── core/
│   │       ├── scraper.py  # GeM API client
│   │       ├── matcher.py  # keyword matching
│   │       └── store.py    # SQLite persistence
│   ├── data/
│   │   ├── products.json   # <-- your keywords go here
│   │   └── bids.db         # created automatically, holds all matches found
│   └── requirements.txt
└── frontend/           # Angular UI
    └── src/app/
        ├── app.ts / app.html          # main page, filters, pagination
        ├── services/bid.service.ts    # calls the backend
        └── components/
            ├── filter-bar/            # search, ministry, keyword, date filters
            └── bid-table/             # the results table
```

## How to run it

You need two terminals open at the same time — the backend and the frontend
are separate processes that talk to each other over `localhost`.

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows — use `source venv/bin/activate` on Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

This starts the API at `http://localhost:8000`. It does **not** fetch
anything from GeM automatically — that only happens when you click
**Check now** in the UI (or `POST` to `/check-now` directly).

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm start
```

Open **http://localhost:4200** in your browser. It loads whatever's already
been found (empty on first run) and lets you filter/search/paginate.

### 3. Find your bids

Click **Check now**. This fetches every ongoing bid for your configured
state(s), checks each one against your keywords, and saves any matches —
new matches show up in the table once it finishes. On later runs, only
bids not seen before are treated as "new" (dedup happens automatically via
`bid_no`), but *all* matches — old and new — stay visible in the table.

## Where to add your keywords

Edit **`backend/data/products.json`**. It's a simple list — one entry per
keyword or phrase you want matched against a bid's item description:

```json
{
  "keywords": [
    "defibrillator",
    "led lighting",
    "hard disk drive"
  ]
}
```

**How matching works:** it's a case-insensitive *substring* check against
each bid's item text — not exact match, not fuzzy/synonym-aware. `"led
light"` matches "**Portable Emergency LED Light** Tower System," but won't
match "LED **Lighting**" unless you add that as a separate entry too. A few
tips:

- List real variants separately — e.g. both `"led light"` and `"led
  lighting"` if you want either form covered.
- Keep entries specific enough to avoid noise (a keyword like `"cable"` will
  match almost anything) but general enough to catch real variants of your
  product.
- No restart needed after editing — just click **Check now** again (or
  re-run it) and the new keyword list is used immediately, since it's read
  fresh from the file on every check.

## Which states are searched

Edit `STATES` in **`backend/app/config.py`**:

```python
STATES = [
    "JAMMU & KASHMIR",
]
```

Add more states to that list (matching GeM's exact naming) to search
multiple regions in one check.

## If GeM changes their site and it stops working

This project works by replaying GeM's own internal search request (found via
browser DevTools), not an official public API — so if GeM changes their
frontend, the two things most likely to break are in `backend/app/config.py`:

- `CSRF_COOKIE_NAME` — the cookie the security token comes from
- `CSRF_FIELD_NAME` — the form field name that token must also be sent as

Re-check these via DevTools → Network tab → the `search-bids` request →
Headers (for the cookie) and Payload (for the field name), and update
`config.py` to match.
