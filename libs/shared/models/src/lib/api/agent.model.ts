export const AgentStatusEnum = {
  Completed: 'completed',
  Running: 'running',
  Failed: 'failed',
} as const;

export type AgentStatus =
  (typeof AgentStatusEnum)[keyof typeof AgentStatusEnum];

export type AgentResponse<T> = {
  status: AgentStatus;
  result: T;
};
