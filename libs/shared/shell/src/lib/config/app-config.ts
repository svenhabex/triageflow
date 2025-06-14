import { InjectionToken } from '@angular/core';

import { AppConfig } from './app-config.types';

export const APP_CONFIG = new InjectionToken<AppConfig>('Application config');
