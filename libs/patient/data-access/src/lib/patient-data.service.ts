import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  StartIntakeRequest,
  StartIntakeResponse,
} from '@triageflow/shared/models';

@Injectable({ providedIn: 'root' })
export class PatientDataService {
  readonly #http = inject(HttpClient);

  startIntake(request: StartIntakeRequest): Observable<StartIntakeResponse> {
    return this.#http.post<StartIntakeResponse>(
      'agents/patient/intake',
      request,
    );
  }
}
