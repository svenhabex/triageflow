import { PanelModule } from 'primeng/panel';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { Component, computed, input } from '@angular/core';
import { IntakeResult } from '@triageflow/shared/models';

@Component({
  selector: 'flow-intake-result',
  templateUrl: 'intake-result.component.html',
  imports: [TagModule, ProgressBarModule, PanelModule],
})
export class IntakeResultComponent {
  readonly result = input.required<IntakeResult>();

  readonly painLevel = computed(() => (this.result().painLevel ?? 0) * 10);
  readonly painLevelColor = computed(() => {
    if (this.painLevel() < 30) return '#22c55e';
    if (this.painLevel() < 70) return '#f97316';
    return '#ef4444';
  });
  readonly painLevelDescription = computed(() => {
    if (this.painLevel() < 30) return 'Mild';
    if (this.painLevel() < 70) return 'Moderate';
    return 'Severe';
  });
}
