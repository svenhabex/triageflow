import { Route } from '@angular/router';
import { MainShellComponent } from '@triageflow/shared/shell';

export const routes: Route[] = [
  {
    path: '',
    component: MainShellComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
    ],
  },
];
