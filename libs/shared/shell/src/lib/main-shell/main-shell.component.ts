import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../../../../ui/src/lib/sidebar/sidebar.component';
import { NavigationItem, FlowTypeEnum } from '@triageflow/shared/models';

@Component({
  selector: 'flow-main-shell',
  templateUrl: 'main-shell.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SidebarComponent, RouterOutlet],
})
export class MainShellComponent {
  navigationItems: NavigationItem[] = [
    {
      label: 'Queue',
      icon: 'pi-list',
      route: '/queue',
    },
  ];

  flows = [
    {
      label: 'Emergency room triage',
      type: FlowTypeEnum.ER_PATIENT,
      items: [
        {
          id: '1',
          name: 'Piet Pietersen',
          description: 'Analyzing symptoms',
          icon: 'pi-user',
        },
        {
          id: '2',
          name: 'Jan Jansen',
          description: 'Analyzing symptoms',
          icon: 'pi-user',
        },
        {
          id: '3',
          name: 'Karel Klaassen',
          description: 'Analyzing symptoms',
          icon: 'pi-user',
        },
      ],
    },
  ];
}
