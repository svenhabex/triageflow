export const FlowTypeEnum = {
  ER_PATIENT: 'ErTriage',
} as const;
export type FlowType = (typeof FlowTypeEnum)[keyof typeof FlowTypeEnum];

export type FlowList = {
  label: string;
  type: FlowType;
  items: FlowListItem[];
};

export type FlowListItem = {
  id: string;
  name: string;
  description: string;
  icon: string;
};
