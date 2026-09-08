import { Component, computed, effect, input, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatchedBid } from '../../models/bid.model';
import { BidService } from '../../services/bid.service';

const PAGE_SIZE = 10;

@Component({
  selector: 'app-bid-table',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './bid-table.html',
})
export class BidTable {
  bids = input<MatchedBid[]>([]);
  pageSize = PAGE_SIZE;

  private currentPageRaw = signal(1);

  totalPages = computed(() => Math.max(1, Math.ceil(this.bids().length / this.pageSize)));

  // Clamped so a stale page number can never point past the end (e.g. if a
  // filter shrinks the result set while you're on page 4).
  currentPage = computed(() => Math.min(this.currentPageRaw(), this.totalPages()));

  pagedBids = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize;
    return this.bids().slice(start, start + this.pageSize);
  });

  rangeStart = computed(() => (this.bids().length === 0 ? 0 : (this.currentPage() - 1) * this.pageSize + 1));
  rangeEnd = computed(() => Math.min(this.currentPage() * this.pageSize, this.bids().length));

  constructor(private bidService: BidService) {
    // Any time the filtered bid list changes (new search/filter/date range,
    // or a fresh "Check now" result), jump back to page 1 rather than
    // stranding the user on a page that may no longer make sense.
    effect(() => {
      this.bids();
      this.currentPageRaw.set(1);
    });
  }

  bidLink(bid: MatchedBid): string {
    return this.bidService.bidLink(bid);
  }

  prevPage(): void {
    this.currentPageRaw.set(Math.max(1, this.currentPage() - 1));
  }

  nextPage(): void {
    this.currentPageRaw.set(Math.min(this.totalPages(), this.currentPage() + 1));
  }
}