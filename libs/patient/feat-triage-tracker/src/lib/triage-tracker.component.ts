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
  effect,
  ElementRef,
  inject,
  input,
  ViewChild,
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
import {
  CoordinatorResultComponent,
  IntakeResultComponent,
  TriageResultComponent,
} from '@triageflow/patient/ui';
import {
  AgentNameEnum,
  MessageSenderEnum,
  TriageMessageTypeEnum,
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
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MessageBubbleComponent,
    ChatLoadingComponent,
    ReactiveFormsModule,
    ButtonModule,
    IntakeResultComponent,
    TriageResultComponent,
    CoordinatorResultComponent,
  ],
  providers: [providePatientDataAccess()],
  host: { class: 'flex items-end py-8 mx-auto max-w-[1000px] min-h-full' },
})
export class TriageTrackerComponent {
  readonly #patientDataFacade = inject(PatientDataFacade);

  @ViewChild('scrollContainer') scrollContainer!: ElementRef<HTMLDivElement>;

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
          sessionId: this.sessionId(),
          type: TriageMessageTypeEnum.startWorkflow,
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
      map((response) => {
        if (response.type === TriageMessageTypeEnum.responseAgent) {
          switch (response.name) {
            case AgentNameEnum.intake:
              return {
                type: TriageTrackerOutputTypeEnum.Intake,
                data: response.data,
              } as TriageTrackerOutput;
            case AgentNameEnum.triage:
              return {
                type: TriageTrackerOutputTypeEnum.Triage,
                data: response.data,
              } as TriageTrackerOutput;
            case AgentNameEnum.coordinator:
              return {
                type: TriageTrackerOutputTypeEnum.Coordinator,
                data: response.data,
              } as TriageTrackerOutput;
            default:
              return null;
          }
        } else {
          return null;
        }
      }),
      filter((output): output is TriageTrackerOutput => output !== null),
    );

  readonly isLoading = toSignal(
    merge(
      this.userMessages$.pipe(map(() => true)),
      this.webSocketSubject$.pipe(
        switchMap((webSocketSubject) => webSocketSubject.asObservable()),
        map((response) => {
          if (
            response.type === TriageMessageTypeEnum.runningAgent ||
            response.type === TriageMessageTypeEnum.startAgent
          ) {
            return true;
          }

          return false;
        }),
      ),
    ),
    { initialValue: false },
  );

  readonly loadingText = toSignal(
    this.webSocketSubject$.pipe(
      switchMap((webSocketSubject) => webSocketSubject.asObservable()),
      map((response) => {
        if (
          response.type === TriageMessageTypeEnum.runningAgent &&
          response.name === AgentNameEnum.intake
        ) {
          return `...Extracting patient information...`;
        }

        if (
          response.type === TriageMessageTypeEnum.runningAgent &&
          response.name === AgentNameEnum.triage
        ) {
          return `...Assessing patient's condition...`;
        }

        if (
          response.type === TriageMessageTypeEnum.runningAgent &&
          response.name === AgentNameEnum.coordinator
        ) {
          return `...Assigning staff...`;
        }

        if (response.type === TriageMessageTypeEnum.startWorkflow) {
          return 'Starting workflow...';
        }

        return 'Processing...';
      }),
    ),
  );

  readonly output$ = merge(
    this.userMessageWithSideEffect$,
    this.agentResponses$,
  ).pipe(
    scan((acc, curr) => [...acc, curr], [] as TriageTrackerOutput[]),
    tap((output) => {
      console.log('output', output);
    }),
    share(),
  );

  readonly showConversationForm = toSignal(
    this.output$.pipe(map((output) => output.length <= 0)),
    { initialValue: true },
  );

  readonly output = toSignal(this.output$, { initialValue: [] });

  readonly form = new FormGroup({
    message: new FormControl('', [Validators.required]),
  });

  protected readonly TriageTrackerOutputTypeEnum = TriageTrackerOutputTypeEnum;

  constructor() {
    // Auto-scroll to bottom when output changes
    effect(() => {
      const outputItems = this.output();
      if (outputItems.length > 0 && this.scrollContainer) {
        setTimeout(() => {
          this.scrollContainer.nativeElement.scrollTop =
            this.scrollContainer.nativeElement.scrollHeight;
        }, 0);
      }
    });
  }

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
