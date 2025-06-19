import { Observable } from 'rxjs';
import { WebSocketSubject } from 'rxjs/webSocket';
import { inject, Injectable } from '@angular/core';
import {
  StartIntakeRequest,
  IntakeResponseDTO,
  WebSocketTriageDTO,
} from '@triageflow/shared/models';

import { PatientDataService } from './patient-data.service';

@Injectable()
export class PatientDataFacade {
  readonly #patientDataService = inject(PatientDataService);

  startIntake(request: StartIntakeRequest): Observable<IntakeResponseDTO> {
    return this.#patientDataService.startIntake(request);
  }

  openTriageConnection(
    sessionId: string,
  ): WebSocketSubject<WebSocketTriageDTO> {
    return this.#patientDataService.openTriageConnection(sessionId);
  }
}
