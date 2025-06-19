import { Observable } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  StartIntakeRequest,
  IntakeResponseDTO,
  WebSocketTriageDTO,
} from '@triageflow/shared/models';
import { APP_CONFIG } from '@triageflow/shared/shell';

@Injectable()
export class PatientDataService {
  readonly #http = inject(HttpClient);
  readonly #config = inject(APP_CONFIG);

  startIntake(request: StartIntakeRequest): Observable<IntakeResponseDTO> {
    return this.#http.post<IntakeResponseDTO>('agents/patient/intake', request);
  }

  openTriageConnection(
    sessionId: string,
  ): WebSocketSubject<WebSocketTriageDTO> {
    return webSocket(
      `${this.#config.websocketEndpoint}agents/patient/triage/${sessionId}`,
    );
  }
}
