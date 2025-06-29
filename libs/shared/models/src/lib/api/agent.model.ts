import { CoordinatorResponseDTO } from './coordinator.model';
import { IntakeResponseDTO } from './intake.model';
import { TriageResponseDTO } from './triage.model';

export const AgentNameEnum = {
  intake: 'INTAKE',
  triage: 'TRIAGE',
  coordinator: 'COORDINATOR',
} as const;

export type AgentName = (typeof AgentNameEnum)[keyof typeof AgentNameEnum];

export const TriageMessageTypeEnum = {
  startWorkflow: 'START_WORKFLOW',
  runningAgent: 'RUNNING_AGENT',
  startAgent: 'START_AGENT',
  responseAgent: 'RESPONSE_AGENT',
  errorAgent: 'ERROR_AGENT',
  humanApproval: 'HUMAN_APPROVAL',
  endWorkflow: 'END_WORKFLOW',
} as const;

export type TriageMessageType =
  (typeof TriageMessageTypeEnum)[keyof typeof TriageMessageTypeEnum];

export type TriageMessage = {
  sessionId: string;
};

export type StartWorkflowMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.startWorkflow;
  conversation: string;
};

export type RunningAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.runningAgent;
  name: AgentName;
};

export type StartAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.startAgent;
  name: AgentName;
};

export type ResponseAgentMessage =
  | IntakeResponseAgentMessage
  | TriageResponseAgentMessage
  | CoordinatorResponseAgentMessage;

export type IntakeResponseAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.responseAgent;
  name: typeof AgentNameEnum.intake;
  data: IntakeResponseDTO;
};

export type TriageResponseAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.responseAgent;
  name: typeof AgentNameEnum.triage;
  data: TriageResponseDTO;
};

export type CoordinatorResponseAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.responseAgent;
  name: typeof AgentNameEnum.coordinator;
  data: CoordinatorResponseDTO;
};

export type ErrorAgentMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.errorAgent;
  error: string;
};

export type HumanApprovalMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.humanApproval;
  approved: boolean;
};

export type EndWorkflowMessage = TriageMessage & {
  type: typeof TriageMessageTypeEnum.endWorkflow;
};

export type TriageDTO =
  | StartWorkflowMessage
  | RunningAgentMessage
  | StartAgentMessage
  | ResponseAgentMessage
  | ErrorAgentMessage
  | HumanApprovalMessage
  | EndWorkflowMessage;
