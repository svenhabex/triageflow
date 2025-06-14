import { ButtonModule } from 'primeng/button';
import { TextareaModule } from 'primeng/textarea';
import { Subject, Observable, concat, of, merge } from 'rxjs';
import {
  switchMap,
  map,
  scan,
  catchError,
  endWith,
  filter,
  tap,
  startWith,
} from 'rxjs/operators';
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  output,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { ChatService } from './chat.service';
import {
  ChatMessage,
  MessageAction,
  MessageActionTypeEnum,
  MessageSenderEnum,
  MessagesState,
  StreamedChatResponsePart,
  StreamedResponsePartTypeEnum,
} from './chat.types';
import { LoadingDotsComponent } from './loading/loading-dots.component';
import { MessageBubbleComponent } from './message-bubble/message-bubble.component';

@Component({
  selector: 'flow-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss'],
  imports: [
    ReactiveFormsModule,
    TextareaModule,
    ButtonModule,
    MessageBubbleComponent,
    LoadingDotsComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatComponent {
  readonly #chatService = inject(ChatService);

  readonly sendMessage = output<string>();

  readonly form = new FormGroup({
    message: new FormControl('', [Validators.required]),
  });
  readonly sendQueryAction = new Subject<string>();
  readonly messageActions$ = this.getMessageActions();
  readonly messages = toSignal(this.getMessages(), { initialValue: [] });
  readonly #loadingStart$ = this.sendQueryAction.pipe(map(() => true));
  readonly #loadingEnd$ = this.messageActions$.pipe(
    filter(
      (action) =>
        action.type === MessageActionTypeEnum.HandleStreamError ||
        action.type === MessageActionTypeEnum.StreamCompleted,
    ),
    map(() => false),
  );
  readonly isLoading = toSignal(
    merge(this.#loadingStart$, this.#loadingEnd$).pipe(startWith(false)),
    { initialValue: false },
  );

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && event.shiftKey) {
      return;
    }

    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      this.triggerSendMessage();
    }
  }

  triggerSendMessage(): void {
    const messageControl = this.form.get('message');
    this.form.markAllAsTouched();

    if (this.form.invalid || !messageControl?.value) {
      return;
    }

    const userMessageText = messageControl.value.trim();
    if (userMessageText) {
      this.sendQueryAction.next(userMessageText);
    }
  }

  private getMessageActions(): Observable<MessageAction> {
    return this.sendQueryAction.pipe(
      tap(() => this.form.get('message')?.reset()),
      switchMap((query) => {
        const userMessageAction = of({
          type: MessageActionTypeEnum.AddUserMessage,
          text: query,
        });

        const assistantPlaceholderAction = of({
          type: MessageActionTypeEnum.AddAssistantPlaceholder,
        });

        const streamActions$ = this.#chatService.sendMessage(query).pipe(
          map((part) => ({
            type: MessageActionTypeEnum.UpdateAssistantMessage,
            part,
          })),
          catchError((error) =>
            of({ type: MessageActionTypeEnum.HandleStreamError, error }),
          ),
          endWith({ type: MessageActionTypeEnum.StreamCompleted }),
        );

        return concat(
          userMessageAction,
          assistantPlaceholderAction,
          streamActions$,
        );
      }),
    );
  }

  private getMessages(): Observable<ReadonlyArray<ChatMessage>> {
    return this.messageActions$.pipe(
      scan(
        (state: MessagesState, action: MessageAction): MessagesState => {
          switch (action.type) {
            case MessageActionTypeEnum.AddUserMessage:
              return this.addUserMessage(state, action.text);
            case MessageActionTypeEnum.AddAssistantPlaceholder:
              return this.addAssistantPlaceholder(state);
            case MessageActionTypeEnum.UpdateAssistantMessage:
              return this.updateAssistantMessage(state, action.part);
            case MessageActionTypeEnum.HandleStreamError:
              return this.handleStreamError(state, action.error);
            case MessageActionTypeEnum.StreamCompleted:
              return this.handleStreamCompleted(state);
            default:
              return state;
          }
        },
        { messages: [], activeAssistantMessageIndex: null },
      ),
      map((state) => state.messages),
    );
  }

  private addUserMessage(state: MessagesState, text: string): MessagesState {
    return {
      messages: [...state.messages, { text, sender: 'user' }],
      activeAssistantMessageIndex: null,
    };
  }

  private addAssistantPlaceholder(state: MessagesState): MessagesState {
    const newMessages = [...state.messages];
    const newActiveAssistantIndex = newMessages.length;
    newMessages.push({
      text: '',
      sender: 'assistant',
      sources: [],
      isLoading: true,
    });
    return {
      messages: newMessages,
      activeAssistantMessageIndex: newActiveAssistantIndex,
    };
  }

  private updateAssistantMessage(
    state: MessagesState,
    part: StreamedChatResponsePart,
  ): MessagesState {
    if (
      state.activeAssistantMessageIndex === null ||
      !state.messages[state.activeAssistantMessageIndex]
    ) {
      console.error(
        'UpdateAssistantMessage: No active assistant message index or index out of bounds.',
      );

      return state;
    }
    const newMessages = [...state.messages];
    const assistantMsg = { ...newMessages[state.activeAssistantMessageIndex] };

    switch (part.type) {
      case StreamedResponsePartTypeEnum.Sources:
        assistantMsg.sources = part.data;
        break;
      case StreamedResponsePartTypeEnum.Chunk:
        assistantMsg.text += part.data;
        break;
      case StreamedResponsePartTypeEnum.Done:
        assistantMsg.isLoading = false;
        break;
      case StreamedResponsePartTypeEnum.Error:
        console.error('Error in stream part content:', part.error);
        assistantMsg.text = 'Error: Could not get a streamed response.';
        assistantMsg.isLoading = false;
        break;
    }
    newMessages[state.activeAssistantMessageIndex] = assistantMsg;

    return { ...state, messages: newMessages };
  }

  private handleStreamError(
    state: MessagesState,
    error: unknown,
  ): MessagesState {
    console.error('Stream processing error:', error);
    const newMessages = [...state.messages];
    const activeAssistantMessage =
      state.activeAssistantMessageIndex !== null
        ? state.messages[state.activeAssistantMessageIndex]
        : null;

    if (activeAssistantMessage) {
      activeAssistantMessage.text =
        'Error: Failed to connect to streaming service.';
      activeAssistantMessage.isLoading = false;

      return { ...state, messages: newMessages };
    }

    newMessages.push({
      text: 'Error: Failed to connect to streaming service.',
      sender: MessageSenderEnum.Assistant,
      isLoading: false,
    });

    return { ...state, messages: newMessages };
  }

  private handleStreamCompleted(state: MessagesState): MessagesState {
    if (
      state.activeAssistantMessageIndex !== null &&
      state.messages[state.activeAssistantMessageIndex]
    ) {
      const newMessages = [...state.messages];
      const assistantMsg = {
        ...newMessages[state.activeAssistantMessageIndex],
      };
      if (assistantMsg.isLoading) {
        assistantMsg.isLoading = false;
      }
      newMessages[state.activeAssistantMessageIndex] = assistantMsg;

      return { ...state, messages: newMessages };
    }

    return state;
  }
}
