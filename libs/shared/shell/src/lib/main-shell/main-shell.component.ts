import { ChangeDetectionStrategy, Component } from '@angular/core';
import { SidebarComponent } from '../../../../ui/src/lib/sidebar/sidebar.component';

@Component({
  selector: 'flow-main-shell',
  templateUrl: 'main-shell.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SidebarComponent],
})
export class MainShellComponent {}
