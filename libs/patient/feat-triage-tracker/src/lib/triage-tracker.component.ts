import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'flow-triage-tracker',
  templateUrl: 'triage-tracker.component.html',
  styleUrls: ['triage-tracker.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
})
export class TriageTrackerComponent {}
