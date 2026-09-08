export interface MatchedBid {
  bid_no: string;
  bid_id: string;
  items: string;
  quantity: string;
  start_date: string;
  end_date: string;
  ministry: string;
  department: string;
  matched_keywords: string[];
  first_seen_at?: string;
}

export interface MatchesResponse {
  matches: MatchedBid[];
}

export interface CheckResult {
  bids_fetched: number;
  total_matches: number;
  new_matches: MatchedBid[];
}
