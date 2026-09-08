"""
Matches bid 'items' text against your keyword list in data/products.json.

Matching is deliberately simple (case-insensitive substring) so it's
predictable and easy to reason about. If it's too strict/loose once you
see real results, this is the one place to adjust.
"""

import json
from typing import List, Dict, Optional

from app import config


def load_keywords() -> List[str]:
    with open(config.PRODUCTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [k.strip().lower() for k in data.get("keywords", []) if k.strip()]


def find_matches(bids: List[Dict], keywords: Optional[List[str]] = None) -> List[Dict]:
    """
    Returns a list of dicts: each bid that matched, plus which keyword(s)
    triggered it, e.g. {**bid, "matched_keywords": ["defibrillator"]}
    """
    if keywords is None:
        keywords = load_keywords()

    matches = []
    for bid in bids:
        items_text = str(bid.get("items", "")).lower()
        hit_keywords = [kw for kw in keywords if kw in items_text]
        if hit_keywords:
            matches.append({**bid, "matched_keywords": hit_keywords})

    return matches
