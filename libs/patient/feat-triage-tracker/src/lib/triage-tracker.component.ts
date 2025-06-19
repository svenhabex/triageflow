import { ButtonModule } from 'primeng/button';
import {
  filter,
  map,
  merge,
  Observable,
  of,
  scan,
  share,
  Subject,
  switchMap,
  tap,
  withLatestFrom,
} from 'rxjs';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  PatientDataFacade,
  providePatientDataAccess,
} from '@triageflow/patient/data-access';
import { IntakeResultComponent } from '@triageflow/patient/ui';
import {
  AgentNameEnum,
  MessageSenderEnum,
  WebSocketTriageTypeEnum,
} from '@triageflow/shared/models';
import {
  ChatLoadingComponent,
  MessageBubbleComponent,
} from '@triageflow/shared/ui';

import {
  TriageTrackerOutput,
  TriageTrackerOutputTypeEnum,
} from './triage-tracker.model';
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
  providers: [providePatientDataAccess()],
})
export class TriageTrackerComponent {
  readonly #patientDataFacade = inject(PatientDataFacade);

  readonly id = input<string | null>(null);

  readonly sessionId = computed(() => this.id() ?? window.crypto.randomUUID());
  readonly userMessages$ = new Subject<string>();
  readonly webSocketSubject$ = toObservable(this.sessionId).pipe(
    switchMap((sessionId) =>
      of(this.#patientDataFacade.openTriageConnection(sessionId)),
    ),
    share(),
  );

  private readonly userMessageWithSideEffect$: Observable<TriageTrackerOutput> =
    this.userMessages$.pipe(
      withLatestFrom(this.webSocketSubject$),
      tap(([message, webSocketSubject]) => {
        webSocketSubject.next({
          type: WebSocketTriageTypeEnum.startWorkflow,
          conversation: message,
        });
      }),
      map(([message]) => ({
        type: TriageTrackerOutputTypeEnum.Message,
        data: { type: MessageSenderEnum.Human, content: message },
      })),
    );

  private readonly agentResponses$: Observable<TriageTrackerOutput> =
    this.webSocketSubject$.pipe(
      switchMap((webSocketSubject) => webSocketSubject.asObservable()),
      filter(
        (response) => response.type === WebSocketTriageTypeEnum.responseAgent,
      ),
      map((response) => {
        switch (response.name) {
          case AgentNameEnum.intake:
            return {
              type: TriageTrackerOutputTypeEnum.Intake,
              data: response.data,
            } as TriageTrackerOutput;
          default:
            return null;
        }
      }),
      filter((output): output is TriageTrackerOutput => output !== null),
    );

  readonly output$ = merge(
    this.userMessageWithSideEffect$,
    this.agentResponses$,
  ).pipe(
    scan((acc, curr) => [...acc, curr], [] as TriageTrackerOutput[]),
    share(),
  );

  readonly output = toSignal(this.output$, { initialValue: [] });

  readonly isLoading = toSignal(
    merge(
      this.userMessages$.pipe(map(() => true)),
      this.output$.pipe(map(() => false)),
    ),
    { initialValue: false },
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
      this.userMessages$.next(userMessageText);
    }
  }
}
