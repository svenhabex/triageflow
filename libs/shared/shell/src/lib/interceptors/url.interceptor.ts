import {
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';

import { APP_CONFIG } from '../config/app-config';

export const urlInterceptor: HttpInterceptorFn = (
  request: HttpRequest<unknown>,
  next: HttpHandlerFn,
) => {
  const config = inject(APP_CONFIG);

  if (request.url.startsWith('./assets')) {
    return next(request);
  }

  const apiEndpoint = config.apiEndpoint.endsWith('/')
    ? config.apiEndpoint
    : `${config.apiEndpoint}/`;
  const url = request.url.startsWith('/') ? request.url.slice(1) : request.url;

  request = request.clone({ url: apiEndpoint + url });

  return next(request);
};
