import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  AgentResponse,
  StartIntakeRequest,
  StartIntakeResult,
} from '@triageflow/shared/models';

@Injectable({ providedIn: 'root' })
export class PatientDataService {
  readonly #http = inject(HttpClient);

  startIntake(
    request: StartIntakeRequest,
  ): Observable<AgentResponse<StartIntakeResult>> {
    return this.#http.post<AgentResponse<StartIntakeResult>>(
      'agents/patient/intake',
      request,
    );
  }
}
