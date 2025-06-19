import { Provider } from '@angular/core';

import { PatientDataFacade } from './patient-data.facade';
import { PatientDataService } from './patient-data.service';

export function providePatientDataAccess(): Provider[] {
  return [PatientDataService, PatientDataFacade];
}
