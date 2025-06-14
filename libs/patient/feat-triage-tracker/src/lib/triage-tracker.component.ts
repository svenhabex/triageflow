import { ButtonModule } from 'primeng/button';
import { map, merge, Observable, scan, Subject, switchMap } from 'rxjs';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { PatientDataService } from '@triageflow/patient/data-access';
import { ChatMessage, MessageSenderEnum } from '@triageflow/shared/models';
import {
  ChatLoadingComponent,
  MessageBubbleComponent,
} from '@triageflow/shared/ui';

@Component({
  selector: 'flow-triage-tracker',
  templateUrl: 'triage-tracker.component.html',
  styleUrls: ['triage-tracker.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MessageBubbleComponent,
    ChatLoadingComponent,
    ReactiveFormsModule,
    ButtonModule,
  ],
})
export class TriageTrackerComponent {
  readonly #patientDataService = inject(PatientDataService);

  readonly sumbitMessage$ = new Subject<string>();
  readonly userMessages$ = this.getUserMessages();
  readonly assistantMessages$ = this.getAssistantMessages();
  readonly messages = toSignal(
    this.getMessages(this.userMessages$, this.assistantMessages$),
  );
  readonly isLoading = toSignal(
    this.getLoading(this.userMessages$, this.assistantMessages$),
  );

  readonly form = new FormGroup({
    message: new FormControl('', [Validators.required]),
  });

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
    this.form.reset();

    if (userMessageText) {
      this.sumbitMessage$.next(userMessageText);
    }
  }

  private getUserMessages(): Observable<ChatMessage[]> {
    return this.sumbitMessage$.pipe(
      map((message) => [{ content: message, sender: MessageSenderEnum.User }]),
    );
  }

  private getAssistantMessages(): Observable<ChatMessage[]> {
    return this.sumbitMessage$.pipe(
      switchMap((message) =>
        this.#patientDataService.startIntake({ conversation: message }).pipe(
          map((response) => [
            {
              content: response.result.message,
              sender: MessageSenderEnum.Assistant,
            },
          ]),
        ),
      ),
    );
  }

  private getMessages(
    userMessages: Observable<ChatMessage[]>,
    assistantMessages: Observable<ChatMessage[]>,
  ): Observable<ChatMessage[]> {
    return merge(userMessages, assistantMessages).pipe(
      scan((acc, curr) => [...acc, ...curr], [] as ChatMessage[]),
    );
  }

  private getLoading(
    userMessages: Observable<ChatMessage[]>,
    assistantMessages: Observable<ChatMessage[]>,
  ): Observable<boolean> {
    return merge(
      userMessages.pipe(map(() => true)),
      assistantMessages.pipe(map(() => false)),
    );
  }
}
