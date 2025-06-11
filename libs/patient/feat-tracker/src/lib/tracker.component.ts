import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'flow-tracker',
  templateUrl: 'tracker.component.html',
  styleUrls: ['tracker.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
})
export class TrackerComponent {}
