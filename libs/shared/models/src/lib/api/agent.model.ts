import { IntakeResponseDTO } from './intake.model';

export const AgentNameEnum = {
  intake: 'INTAKE',
  triage: 'TRIAGE',
  coordinator: 'COORDINATOR',
} as const;

export type AgentName = (typeof AgentNameEnum)[keyof typeof AgentNameEnum];

export const WebSocketTriageTypeEnum = {
  startWorkflow: 'START_WORKFLOW',
  runningAgent: 'RUNNING_AGENT',
  startAgent: 'START_AGENT',
  responseAgent: 'RESPONSE_AGENT',
  errorAgent: 'ERROR_AGENT',
  humanApproval: 'HUMAN_APPROVAL',
  endWorkflow: 'END_WORKFLOW',
} as const;

export type WebSocketTriageType =
  (typeof WebSocketTriageTypeEnum)[keyof typeof WebSocketTriageTypeEnum];

export type WebSocketTriageDTO =
  | {
      type: typeof WebSocketTriageTypeEnum.startWorkflow;
      conversation: string;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.runningAgent;
      name: AgentName;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.startAgent;
      name: AgentName;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.responseAgent;
      name: typeof AgentNameEnum.intake;
      data: IntakeResponseDTO;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.errorAgent;
      error: string;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.humanApproval;
      approved: boolean;
    }
  | {
      type: typeof WebSocketTriageTypeEnum.endWorkflow;
    };
