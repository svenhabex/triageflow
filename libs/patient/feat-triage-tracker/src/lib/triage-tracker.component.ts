import { ButtonModule } from 'primeng/button';
import { map, merge, Observable, scan, share, Subject, switchMap } from 'rxjs';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { PatientDataService } from '@triageflow/patient/data-access';
import { IntakeResultComponent } from '@triageflow/patient/ui';
import {
  AgentResponse,
  AgentStatusEnum,
  ChatMessage,
  IntakeResponse,
  IntakeResult,
  MessageSenderEnum,
} from '@triageflow/shared/models';
import {
  ChatLoadingComponent,
  MessageBubbleComponent,
} from '@triageflow/shared/ui';

import {
  TriageTrackerOutput,
  TriageTrackerOutputTypeEnum,
} from './triage-tracker.model';

const chatMessageMock: ChatMessage = {
  content: 'Hello, how are you?',
  type: MessageSenderEnum.Human,
  id: '1',
};

const intakeAgentResponseMock: IntakeResponse = {
  status: AgentStatusEnum.Completed,
  messages: [],
  errors: [],
  lastNode: 'intake',
  result: {
    symptoms: ['chest pain', 'dizzy'],
    painLevel: 8,
    chiefComplaint: 'Patient presents with chest pain.',
    medications: ['ibuprofen', 'aspirin'],
    allergies: ['penicillin'],
    additionalNotes: 'Patient consumed 8 to 10 beers.',
  },
};

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
    IntakeResultComponent,
  ],
})
export class TriageTrackerComponent {
  readonly #patientDataService = inject(PatientDataService);

  readonly sumbitMessage$ = new Subject<string>();
  readonly userMessages$ = this.getUserMessages();
  readonly assistantResponse$ = this.getAssistantResponse();
  readonly output = toSignal(
    this.getOutput(this.userMessages$, this.assistantResponse$),
  );
  readonly isLoading = toSignal(
    this.getLoading(this.userMessages$, this.assistantResponse$),
  );

  readonly form = new FormGroup({
    message: new FormControl('', [Validators.required]),
  });

  protected readonly TriageTrackerOutputTypeEnum = TriageTrackerOutputTypeEnum;

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
      map((message) => [
        { content: message, type: MessageSenderEnum.Human, id: '' },
      ]),
    );
  }

  private getAssistantResponse(): Observable<AgentResponse<IntakeResult>> {
    return this.sumbitMessage$.pipe(
      switchMap((message) =>
        this.#patientDataService.startIntake({ conversation: message }),
      ),
      share(),
    );
  }

  private getOutput(
    userMessages: Observable<ChatMessage[]>,
    assistantResponse: Observable<AgentResponse<IntakeResult>>,
  ): Observable<TriageTrackerOutput[]> {
    return merge(
      userMessages.pipe(
        map((messages) =>
          messages.map((message) => ({
            type: TriageTrackerOutputTypeEnum.Message,
            data: message,
          })),
        ),
        // startWith([
        //   {
        //     type: TriageTrackerOutputTypeEnum.Message,
        //     data: chatMessageMock,
        //   } as TriageTrackerOutput,
        // ]),
      ),
      assistantResponse.pipe(
        map((response) => [
          {
            type: TriageTrackerOutputTypeEnum.Intake,
            data: response,
          },
        ]),
        // startWith([
        //   {
        //     type: TriageTrackerOutputTypeEnum.Intake,
        //     data: intakeAgentResponseMock,
        //   } as TriageTrackerOutput,
        // ]),
      ),
    ).pipe(scan((acc, curr) => [...acc, ...curr], [] as TriageTrackerOutput[]));
  }

  private getLoading(
    userMessages: Observable<ChatMessage[]>,
    assistantResponse: Observable<AgentResponse<IntakeResult>>,
  ): Observable<boolean> {
    return merge(
      userMessages.pipe(map(() => true)),
      assistantResponse.pipe(map(() => false)),
    );
  }
}
