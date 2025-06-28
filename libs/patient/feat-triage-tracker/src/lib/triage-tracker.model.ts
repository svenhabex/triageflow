import {
  ChatMessage,
  IntakeResponseDTO,
  TriageResponseDTO,
} from '@triageflow/shared/models';

export const TriageTrackerOutputTypeEnum = {
  Intake: 'INTAKE',
  Triage: 'TRIAGE',
  Message: 'MESSAGE',
} as const;

export type TriageTrackerOutputType =
  (typeof TriageTrackerOutputTypeEnum)[keyof typeof TriageTrackerOutputTypeEnum];

export type TriageTrackerOutput =
  | {
      type: typeof TriageTrackerOutputTypeEnum.Intake;
      data: IntakeResponseDTO;
    }
  | {
      type: typeof TriageTrackerOutputTypeEnum.Triage;
      data: TriageResponseDTO;
    }
  | {
      type: typeof TriageTrackerOutputTypeEnum.Message;
      data: ChatMessage;
    };
