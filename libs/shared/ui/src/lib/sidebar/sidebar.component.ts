import { NgOptimizedImage } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NavigationComponent } from '../navigation/navigation.component';
import { NavigationItem } from '@triageflow/shared/models';

@Component({
  selector: 'flow-sidebar',
  templateUrl: 'sidebar.component.html',
  host: {
    class: 'block',
  },
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgOptimizedImage, NavigationComponent],
})
export class SidebarComponent {
  items: NavigationItem[] = [
    {
      label: 'Home',
      icon: 'home',
      route: '/',
    },
  ];
}
