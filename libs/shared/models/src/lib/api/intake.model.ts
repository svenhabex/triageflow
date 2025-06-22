export type StartIntakeRequest = {
  conversation: string;
};

export type PatientInfo = {
  patientId: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  medicalHistory: string[];
  medications: string[];
};

export type IntakeResponseDTO = {
  symptoms: string[];
  painLevel: number;
  chiefComplaint: string;
  medications: string[];
  allergies: string[];
  additionalNotes: string;
  patientInfo: PatientInfo | null;
};
