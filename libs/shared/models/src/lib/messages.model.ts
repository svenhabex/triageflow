export const MessageSenderEnum = {
  Human: 'human',
  Assistant: 'assistant',
} as const;

export type MessageSender =
  (typeof MessageSenderEnum)[keyof typeof MessageSenderEnum];

export type ChatMessage = {
  id: string;
  content: string;
  type: MessageSender;
};
