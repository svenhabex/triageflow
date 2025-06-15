import { AgentResponse } from './agent.model';

export type StartIntakeRequest = {
  conversation: string;
};

export type StartIntakeResult = AgentResponse<{
  symptoms: string[];
  painLevel: number;
  chiefComplaint: string;
  additionalNotes: string;
}>;
