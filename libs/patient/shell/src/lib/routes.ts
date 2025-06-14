import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'tracker',
    pathMatch: 'full',
  },
  {
    path: 'tracker',
    loadComponent: async () =>
      (await import('@triageflow/patient/feat-triage-tracker'))
        .TriageTrackerComponent,
  },
];
