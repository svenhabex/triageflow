import { AgentResponse } from './agent.model';

export type StartIntakeRequest = {
  conversation: string;
};

export type StartIntakeResponse = AgentResponse<{
  message: string;
  symptoms: string[];
}>;
