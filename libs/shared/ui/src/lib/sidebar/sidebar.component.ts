import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'flow-sidebar',
  templateUrl: 'sidebar.component.html',
  styleUrls: ['sidebar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
})
export class SidebarComponent {}
