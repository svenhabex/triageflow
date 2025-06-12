import { NgOptimizedImage } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import { NavigationComponent } from '../navigation/navigation.component';
import { FlowList, FlowType, NavigationItem } from '@triageflow/shared/models';
import { ButtonModule } from 'primeng/button';

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

  onAddFlow(type: FlowType) {
    this.addFlow.emit(type);
  }
}
