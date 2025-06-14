import { ButtonModule } from 'primeng/button';
import { NgOptimizedImage } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  output,
} from '@angular/core';
import { Router } from '@angular/router';
import { FlowList, FlowType, NavigationItem } from '@triageflow/shared/models';

import { NavigationComponent } from '../navigation/navigation.component';

@Component({
  selector: 'flow-sidebar',
  templateUrl: 'sidebar.component.html',
  host: {
    class: 'block',
  },
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgOptimizedImage, NavigationComponent, ButtonModule],
})
export class SidebarComponent {
  readonly #router = inject(Router);

  readonly navigationItems = input<NavigationItem[]>([]);
  readonly flows = input<FlowList[]>([]);

  readonly addFlow = output<FlowType>();

  readonly flowNavigationItems = computed(() => {
    return this.flows().map((flow) => ({
      ...flow,
      items: flow.items.map((item) => ({
        label: item.name,
        icon: item.icon,
        route: `/flows/${item.id}`,
      })),
    }));
  });

  onAddFlow(type: FlowType): void {
    this.#router.navigate(['/patient/tracker'], {
      state: { flowType: type },
    });
  }
}
