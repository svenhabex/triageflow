import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NavigationItem } from '@triageflow/shared/models';

@Component({
  selector: 'flow-navigation',
  templateUrl: 'navigation.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive],
})
export class NavigationComponent {
  items = input.required<NavigationItem[]>();
}
