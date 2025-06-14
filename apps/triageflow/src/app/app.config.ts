import { providePrimeNG } from 'primeng/config';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  provideExperimentalZonelessChangeDetection,
} from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { APP_CONFIG, urlInterceptor } from '@triageflow/shared/shell';

import { routes } from './app.routes';
import { environment } from '../environments/environment.dev';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    provideHttpClient(withInterceptors([urlInterceptor])),
    provideRouter(routes),
    provideAnimationsAsync(),
    providePrimeNG(),
    { provide: APP_CONFIG, useValue: environment },
  ],
};
