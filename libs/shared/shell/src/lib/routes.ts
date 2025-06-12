import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'flows',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: 'flows',
  },
];
