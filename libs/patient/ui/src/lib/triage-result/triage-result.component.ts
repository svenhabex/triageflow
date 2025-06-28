import { PanelModule } from 'primeng/panel';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { Component, input, computed } from '@angular/core';
import { TriageResponseDTO } from '@triageflow/shared/models';

@Component({
  selector: 'flow-triage-result',
  templateUrl: 'triage-result.component.html',
  styleUrl: 'triage-result.component.scss',
  imports: [TagModule, ProgressBarModule, PanelModule],
})
export class TriageResultComponent {
  readonly result = input.required<TriageResponseDTO>();

  readonly progressValue = computed(() =>
    Math.min(Math.max(((this.result().riskLevel - 1) / 4) * 100, 0), 100),
  );

  readonly progressColor = computed(() => {
    if (this.result().riskLevel <= 1) return '#22c55e';
    if (this.result().riskLevel <= 2) return '#eab308';
    if (this.result().riskLevel <= 3) return '#f97316';
    if (this.result().riskLevel <= 4) return '#ef4444';
    return '#dc2626';
  });

  // Computed signal for progress bar CSS class based on risk level
  readonly progressBarClass = computed(() => {
    const riskLevel = this.result().riskLevel;
    if (riskLevel <= 1) return 'progress-level-1';
    if (riskLevel <= 2) return 'progress-level-2';
    if (riskLevel <= 3) return 'progress-level-3';
    if (riskLevel <= 4) return 'progress-level-4';
    return 'progress-level-5';
  });

  readonly levelIndicators = computed(() => {
    const currentLevel = this.result().riskLevel;
    return Array.from({ length: 5 }, (_, i) => ({
      level: i + 1,
      isActive: i + 1 <= currentLevel,
      isCurrentLevel: i + 1 === Math.floor(currentLevel),
    }));
  });

  readonly riskLevelDescription = computed(() => {
    const riskLevel = this.result().riskLevel;
    if (riskLevel <= 1) return 'ESI 1';
    if (riskLevel <= 2) return 'ESI 2';
    if (riskLevel <= 3) return 'ESI 3';
    if (riskLevel <= 4) return 'ESI 4';
    return 'ESI 5';
  });
}
