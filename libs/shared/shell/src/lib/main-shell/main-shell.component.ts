import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../../../../ui/src/lib/sidebar/sidebar.component';

@Component({
  selector: 'flow-main-shell',
  templateUrl: 'main-shell.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SidebarComponent, RouterOutlet],
})
export class MainShellComponent {}
