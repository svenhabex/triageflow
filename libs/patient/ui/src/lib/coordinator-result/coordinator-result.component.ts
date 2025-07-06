import { ButtonModule } from 'primeng/button';
import { PanelModule } from 'primeng/panel';
import { ProgressBarModule } from 'primeng/progressbar';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { Component, input, output } from '@angular/core';
import { CoordinatorResponseDTO, StaffMember } from '@triageflow/shared/models';

@Component({
  selector: 'flow-coordinator-result',
  templateUrl: 'coordinator-result.component.html',
  imports: [
    TagModule,
    ProgressBarModule,
    PanelModule,
    TableModule,
    ButtonModule,
  ],
})
export class CoordinatorResultComponent {
  readonly result = input.required<CoordinatorResponseDTO>();

  readonly assignStaff = output<StaffMember>();

  onAssignStaff(staff: StaffMember): void {
    this.assignStaff.emit(staff);
  }
}
