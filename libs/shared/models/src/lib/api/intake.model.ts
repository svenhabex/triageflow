import { AgentResponse } from './agent.model';

export type StartIntakeRequest = {
  conversation: string;
};

export type IntakeResult = {
  symptoms: string[];
  painLevel: number;
  chiefComplaint: string;
  medications: string[];
  allergies: string[];
  additionalNotes: string;
};

export type IntakeResponse = AgentResponse<IntakeResult>;
