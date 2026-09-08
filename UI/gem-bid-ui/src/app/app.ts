import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { BidService } from './services/bid.service';
import { MatchedBid } from './models/bid.model';
import { FilterBar, BidFilters } from './components/filter-bar/filter-bar';
import { BidTable } from './components/bid-table/bid-table';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [DatePipe, FilterBar, BidTable],
  templateUrl: './app.html',
})
export class App implements OnInit {
  private bidService = inject(BidService);

  matches = signal<MatchedBid[]>([]);
  loading = signal(true);
  checking = signal(false);
  error = signal<string | null>(null);
  lastChecked = signal<Date | null>(null);

  filters = signal<BidFilters>({ search: '', ministry: '', keyword: '', dateFrom: '', dateTo: '' });

  ministries = computed(() =>
    Array.from(new Set(this.matches().map((m) => m.ministry).filter(Boolean))).sort()
  );

  keywords = computed(() =>
    Array.from(new Set(this.matches().flatMap((m) => m.matched_keywords))).sort()
  );

  filteredMatches = computed(() => {
    const f = this.filters();
    const term = f.search.trim().toLowerCase();
    const fromDate = f.dateFrom ? new Date(f.dateFrom) : null;
    const toDate = f.dateTo ? new Date(`${f.dateTo}T23:59:59`) : null;

    return this.matches().filter((m) => {
      const matchesSearch =
        !term ||
        m.bid_no.toLowerCase().includes(term) ||
        m.items.toLowerCase().includes(term) ||
        m.department.toLowerCase().includes(term);
      const matchesMinistry = !f.ministry || m.ministry === f.ministry;
      const matchesKeyword = !f.keyword || m.matched_keywords.includes(f.keyword);

      const endDate = m.end_date ? new Date(m.end_date) : null;
      const matchesDateFrom = !fromDate || (endDate !== null && endDate >= fromDate);
      const matchesDateTo = !toDate || (endDate !== null && endDate <= toDate);

      return matchesSearch && matchesMinistry && matchesKeyword && matchesDateFrom && matchesDateTo;
    });
  });

  ngOnInit(): void {
    this.loadMatches();
  }

  loadMatches(): void {
    this.loading.set(true);
    this.error.set(null);
    this.bidService.getMatches().subscribe({
      next: (res) => {
        this.matches.set(res.matches);
        this.loading.set(false);
        this.lastChecked.set(new Date());
      },
      error: () => {
        this.error.set(
          'Could not reach the backend. Make sure "uvicorn app.main:app --reload" is running on localhost:8000.'
        );
        this.loading.set(false);
      },
    });
  }

  runCheckNow(): void {
    this.checking.set(true);
    this.error.set(null);
    this.bidService.checkNow().subscribe({
      next: () => {
        this.checking.set(false);
        this.loadMatches();
      },
      error: () => {
        this.error.set('Check failed — see the uvicorn terminal for details.');
        this.checking.set(false);
      },
    });
  }

  onFiltersChanged(f: BidFilters): void {
    this.filters.set(f);
  }
}