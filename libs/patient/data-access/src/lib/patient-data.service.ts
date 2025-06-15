import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { StartIntakeRequest, IntakeResponse } from '@triageflow/shared/models';

@Injectable({ providedIn: 'root' })
export class PatientDataService {
  readonly #http = inject(HttpClient);

  startIntake(request: StartIntakeRequest): Observable<IntakeResponse> {
    return this.#http.post<IntakeResponse>('agents/patient/intake', request);
  }
}
