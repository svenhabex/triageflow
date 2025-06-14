import { ButtonModule } from 'primeng/button';
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
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
  readonly messages = signal<ChatMessage[]>([
    {
      text: 'Hello, how are you?',
      sender: MessageSenderEnum.User,
    },
    {
      text: 'I am fine, thank you! Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quos. Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quos. Lorem ipsum dolor sit amet consectetur adipisicing elit.',
      sender: MessageSenderEnum.Assistant,
    },
  ]);
  readonly isLoading = signal(false);

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
    if (userMessageText) {
      console.log(userMessageText);
    }
  }
}
