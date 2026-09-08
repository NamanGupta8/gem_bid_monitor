import { Component, input } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatchedBid } from '../../models/bid.model';
import { BidService } from '../../services/bid.service';

@Component({
  selector: 'app-bid-table',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './bid-table.html',
})
export class BidTable {
  bids = input<MatchedBid[]>([]);

  constructor(private bidService: BidService) {}

  bidLink(bid: MatchedBid): string {
    return this.bidService.bidLink(bid);
  }
}
