# GeM Bid Monitor — UI

Angular 21 + Tailwind CSS frontend for the `gem_bid_monitor` FastAPI backend.
Displays matched bids in a filterable table; clicking a bid number opens the
real bid on GeM in a new tab.

## Setup

```bash
npm install
```

## Run

Make sure the backend is running first (from the `gem_bid_monitor` project):

```bash
uvicorn app.main:app --reload
```

Then, from this folder:

```bash
npm start
```

Open **http://localhost:4200**. It talks to the backend at
`http://localhost:8000` (see `src/app/services/bid.service.ts` if you ever
need to change that).

## What's in here

```
src/app/
├── app.ts / app.html          # root: fetches data, holds filter state
├── app.config.ts              # provides HttpClient
├── models/bid.model.ts        # TypeScript shape matching the API
├── services/bid.service.ts    # calls /matches and /check-now
└── components/
    ├── filter-bar/            # search box + ministry/keyword dropdowns
    └── bid-table/             # the table, bid number links to GeM
```

Filtering happens client-side against whatever `/matches` last returned —
no extra backend calls needed when you type in the search box or change a
dropdown. Hitting **Check now** calls `/check-now` on the backend (this can
take a few minutes, since it re-fetches every page from GeM), then reloads
`/matches` once it's done.

## Notes

- Bid numbers link to `https://bidplus.gem.gov.in/showbidDocument/{bid_id}`
  — GeM's document page uses the internal numeric id, not the human-readable
  `GEM/2026/B/...` bid number, so the backend carries both.
- If you see a CORS error in the browser console, check that the backend's
  `main.py` still has `http://localhost:4200` in its `allow_origins` list.
