"""Pydantic models describing the API's response shapes."""

from typing import List, Optional
from pydantic import BaseModel


class Bid(BaseModel):
    bid_no: str
    bid_id: Optional[str] = ""
    items: str
    quantity: Optional[str] = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    ministry: Optional[str] = ""
    department: Optional[str] = ""


class MatchedBid(Bid):
    matched_keywords: List[str] = []


class CheckResult(BaseModel):
    bids_fetched: int
    total_matches: int
    new_matches: List[MatchedBid]


class MatchesResponse(BaseModel):
    matches: List[MatchedBid]
