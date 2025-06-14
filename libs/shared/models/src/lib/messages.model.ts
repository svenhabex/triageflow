export const MessageSenderEnum = {
  User: 'user',
  Assistant: 'assistant',
} as const;

export type MessageSender =
  (typeof MessageSenderEnum)[keyof typeof MessageSenderEnum];

export type ChatMessage = {
  content: string;
  sender: MessageSender;
  isLoading?: boolean;
};
