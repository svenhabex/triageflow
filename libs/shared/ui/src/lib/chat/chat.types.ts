export const MessageSenderEnum = {
  User: 'user',
  Assistant: 'assistant',
} as const;

export type MessageSender =
  (typeof MessageSenderEnum)[keyof typeof MessageSenderEnum];

export type Source = { source: string; content_preview: string };

export const StreamedResponsePartTypeEnum = {
  Sources: 'sources',
  Chunk: 'chunk',
  Done: 'done',
  Error: 'error',
} as const;

export type StreamedSources = {
  type: typeof StreamedResponsePartTypeEnum.Sources;
  data: Source[];
};
export type StreamedChunk = {
  type: typeof StreamedResponsePartTypeEnum.Chunk;
  data: string;
};
export type StreamedDone = {
  type: typeof StreamedResponsePartTypeEnum.Done;
  data: string;
};
export type StreamedError = {
  type: typeof StreamedResponsePartTypeEnum.Error;
  error: string;
};

export type StreamedChatResponsePart =
  | StreamedSources
  | StreamedChunk
  | StreamedDone
  | StreamedError;

export type ChatMessage = {
  text: string;
  sender: MessageSender;
  sources?: Source[];
  isLoading?: boolean;
};

export type MessagesState = {
  messages: ReadonlyArray<ChatMessage>;
  activeAssistantMessageIndex: number | null;
};

export const MessageActionTypeEnum = {
  AddUserMessage: 'addUserMessage',
  AddAssistantPlaceholder: 'addAssistantPlaceholder',
  UpdateAssistantMessage: 'updateAssistantMessage',
  HandleStreamError: 'handleStreamError',
  StreamCompleted: 'streamCompleted',
} as const;

export type MessageAction =
  | { type: typeof MessageActionTypeEnum.AddUserMessage; text: string }
  | { type: typeof MessageActionTypeEnum.AddAssistantPlaceholder }
  | {
      type: typeof MessageActionTypeEnum.UpdateAssistantMessage;
      part: StreamedChatResponsePart;
    }
  | { type: typeof MessageActionTypeEnum.HandleStreamError; error: unknown }
  | { type: typeof MessageActionTypeEnum.StreamCompleted };
