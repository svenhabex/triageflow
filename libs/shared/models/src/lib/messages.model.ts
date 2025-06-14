export const MessageSenderEnum = {
  User: 'user',
  Assistant: 'assistant',
} as const;

export type MessageSender =
  (typeof MessageSenderEnum)[keyof typeof MessageSenderEnum];

export type MessageSource = { source: string; content_preview: string };

export type ChatMessage = {
  text: string;
  sender: MessageSender;
  sources?: MessageSource[];
  isLoading?: boolean;
};
