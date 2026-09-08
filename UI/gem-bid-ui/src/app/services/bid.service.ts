import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CheckResult, MatchedBid, MatchesResponse } from '../models/bid.model';

@Injectable({ providedIn: 'root' })
export class BidService {
  // The FastAPI backend from the gem_bid_monitor project (uvicorn app.main:app)
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getMatches(): Observable<MatchesResponse> {
    return this.http.get<MatchesResponse>(`${this.baseUrl}/matches`);
  }

  checkNow(): Observable<CheckResult> {
    return this.http.post<CheckResult>(`${this.baseUrl}/check-now`, {});
  }

  /** GeM's public bid-document page uses the internal numeric id, not bid_no. */
  bidLink(bid: MatchedBid): string {
    return `https://bidplus.gem.gov.in/showbidDocument/${bid.bid_id}`;
  }
}
