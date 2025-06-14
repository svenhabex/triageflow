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
        redirectTo: 'queue',
      },
      {
        path: 'queue',
        loadChildren: async () =>
          (await import('@triageflow/queue/shell')).routes,
      },
      {
        path: 'patient',
        loadChildren: async () =>
          (await import('@triageflow/patient/shell')).routes,
      },
    ],
  },
];
