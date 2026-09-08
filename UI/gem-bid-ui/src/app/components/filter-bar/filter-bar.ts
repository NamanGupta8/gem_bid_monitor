import { Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

export interface BidFilters {
  search: string;
  ministry: string;
  keyword: string;
  startDateFrom: string; // 'YYYY-MM-DD' or '' for no lower bound
  startDateTo: string;   // 'YYYY-MM-DD' or '' for no upper bound
  endDateFrom: string;   // 'YYYY-MM-DD' or '' for no lower bound
  endDateTo: string;     // 'YYYY-MM-DD' or '' for no upper bound
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
  startDateFrom = signal('');
  startDateTo = signal('');
  endDateFrom = signal('');
  endDateTo = signal('');

  emit(): void {
    this.filtersChanged.emit({
      search: this.search(),
      ministry: this.ministry(),
      keyword: this.keyword(),
      startDateFrom: this.startDateFrom(),
      startDateTo: this.startDateTo(),
      endDateFrom: this.endDateFrom(),
      endDateTo: this.endDateTo(),
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

  onStartDateFromChange(value: string): void {
    this.startDateFrom.set(value);
    this.emit();
  }

  onStartDateToChange(value: string): void {
    this.startDateTo.set(value);
    this.emit();
  }

  onEndDateFromChange(value: string): void {
    this.endDateFrom.set(value);
    this.emit();
  }

  onEndDateToChange(value: string): void {
    this.endDateTo.set(value);
    this.emit();
  }
}