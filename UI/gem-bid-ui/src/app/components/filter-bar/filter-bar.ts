import { Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

export interface BidFilters {
  search: string;
  ministry: string;
  keyword: string;
  dateFrom: string; // 'YYYY-MM-DD' or '' for no lower bound
  dateTo: string;   // 'YYYY-MM-DD' or '' for no upper bound
}

@Component({
  selector: 'app-filter-bar',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './filter-bar.html',
})
export class FilterBar {
  ministries = input<string[]>([]);
  keywords = input<string[]>([]);
  filtersChanged = output<BidFilters>();

  search = signal('');
  ministry = signal('');
  keyword = signal('');
  dateFrom = signal('');
  dateTo = signal('');

  emit(): void {
    this.filtersChanged.emit({
      search: this.search(),
      ministry: this.ministry(),
      keyword: this.keyword(),
      dateFrom: this.dateFrom(),
      dateTo: this.dateTo(),
    });
  }

  onSearchChange(value: string): void {
    this.search.set(value);
    this.emit();
  }

  onMinistryChange(value: string): void {
    this.ministry.set(value);
    this.emit();
  }

  onKeywordChange(value: string): void {
    this.keyword.set(value);
    this.emit();
  }

  onDateFromChange(value: string): void {
    this.dateFrom.set(value);
    this.emit();
  }

  onDateToChange(value: string): void {
    this.dateTo.set(value);
    this.emit();
  }
}