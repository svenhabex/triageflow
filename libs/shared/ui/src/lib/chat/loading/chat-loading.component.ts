import { ProgressBarModule } from 'primeng/progressbar';
import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'flow-chat-loading',
  templateUrl: 'chat-loading.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ProgressBarModule],
})
export class ChatLoadingComponent {}
