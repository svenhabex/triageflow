import { PanelModule } from 'primeng/panel';
import { ProgressBarModule } from 'primeng/progressbar';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { Component, input } from '@angular/core';
import { CoordinatorResponseDTO } from '@triageflow/shared/models';

@Component({
  selector: 'flow-coordinator-result',
  templateUrl: 'coordinator-result.component.html',
  imports: [TagModule, ProgressBarModule, PanelModule, TableModule],
})
export class CoordinatorResultComponent {
  readonly result = input.required<CoordinatorResponseDTO>();
}
