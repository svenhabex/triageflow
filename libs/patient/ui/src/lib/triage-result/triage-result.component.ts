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
    Math.min(Math.max(((5 - this.result().esiLevel) / 4) * 100, 0), 100),
  );
  readonly esiProgressColor = computed(() =>
    this.getEsiClass('progress-level'),
  );
  readonly esiBackgroundColor = computed(() =>
    this.getEsiClass('esi-background-color'),
  );
  readonly esiColor = computed(() => this.getEsiClass('esi-color'));
  readonly esiBorderColor = computed(() =>
    this.getEsiClass('esi-border-color'),
  );
  readonly esiBackgroundColorLight = computed(() =>
    this.getEsiClass('esi-background-light'),
  );
  readonly levelIndicators = computed(() => {
    const currentLevel = this.result().esiLevel;
    return [5, 4, 3, 2, 1].map((level) => ({
      level,
      isActive: level >= currentLevel,
      isCurrentLevel: level === Math.floor(currentLevel),
    }));
  });
  readonly urgencyInfo = computed(() => {
    const esiLevel = this.result().esiLevel;
    if (esiLevel <= 1)
      return {
        description: 'Critical - Immediate',
        icon: 'pi-exclamation-triangle',
      };

    if (esiLevel <= 2)
      return {
        description: 'High Priority - Urgent',
        icon: 'pi-exclamation-circle',
      };

    if (esiLevel <= 3)
      return {
        description: 'Moderate Priority',
        icon: 'pi-info-circle',
      };

    if (esiLevel <= 4)
      return {
        description: 'Low Priority',
        icon: 'pi-clock',
      };

    return {
      description: 'Routine - Non-urgent',
      icon: 'pi-check-circle',
    };
  });

  private getEsiClass(baseClassName: string): string {
    const esiLevel = this.result().esiLevel;
    const levelNumber = Math.min(5, Math.max(1, Math.ceil(esiLevel)));
    return `${baseClassName}-${levelNumber}`;
  }
}
