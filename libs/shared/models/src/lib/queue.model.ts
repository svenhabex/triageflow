export const queueSeverityEnum = {
  ESI1: 'ESI1',
  ESI2: 'ESI2',
  ESI3: 'ESI3',
  ESI4: 'ESI4',
  ESI5: 'ESI5',
} as const;

export type QueueSeverity =
  (typeof queueSeverityEnum)[keyof typeof queueSeverityEnum];

export type PatientQueueItem = {
  id: number;
  name: string;
  description: string;
  type: QueueSeverity;
};
