import {
  AgentResponse,
  ChatMessage,
  IntakeResult,
} from '@triageflow/shared/models';

export const TriageTrackerOutputTypeEnum = {
  Intake: 'intake',
  Message: 'message',
} as const;

export type TriageTrackerOutputType =
  (typeof TriageTrackerOutputTypeEnum)[keyof typeof TriageTrackerOutputTypeEnum];

export type TriageTrackerOutput =
  | {
      type: 'intake';
      data: AgentResponse<IntakeResult>;
    }
  | {
      type: 'message';
      data: ChatMessage;
    };
