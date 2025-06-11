import { Component, input } from '@angular/core';
import { NavigationItem } from '@triageflow/shared/models';

@Component({
  selector: 'flow-navigation',
  templateUrl: 'navigation.component.html',
})
export class NavigationComponent {
  items = input.required<NavigationItem[]>();
}
