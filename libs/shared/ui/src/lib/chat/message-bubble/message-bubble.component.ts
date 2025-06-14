import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
} from '@angular/core';

import { MessageSender, MessageSenderEnum } from '../chat.types';

@Component({
  selector: 'flow-message-bubble',
  templateUrl: './message-bubble.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'flex' },
})
export class MessageBubbleComponent {
  readonly content = input.required<string>();
  readonly type = input.required<MessageSender>();

  readonly typeClasses = computed(() => {
    return this.type() === MessageSenderEnum.User
      ? 'px-5 py-4 rounded-4xl ml-auto bg-primary-100 shadow-sm'
      : 'mr-auto bg-transparent';
  });
}
