export type StartIntakeRequest = {
  conversation: string;
};

export type IntakeResponseDTO = {
  symptoms: string[];
  painLevel: number;
  chiefComplaint: string;
  medications: string[];
  allergies: string[];
  additionalNotes: string;
};
