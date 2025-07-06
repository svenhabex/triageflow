import { interval, startWith, map } from 'rxjs';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  signal,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  PatientQueueItem,
  QueueSeverity,
  queueSeverityEnum,
} from '@triageflow/shared/models';

@Component({
  selector: 'flow-detail',
  templateUrl: 'detail.component.html',
  styleUrls: ['detail.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
})
export class DetailComponent {
  queueItems = signal<PatientQueueItem[]>([
    {
      id: 1,
      name: 'Peter Parker',
      description: 'This is a description',
      type: queueSeverityEnum.ESI1,
    },
    {
      id: 2,
      name: 'Bruce Wayne',
      description: 'This is a description',
      type: queueSeverityEnum.ESI2,
    },
    {
      id: 3,
      name: 'Clark Kent',
      description: 'This is a description',
      type: queueSeverityEnum.ESI3,
    },
    {
      id: 4,
      name: 'Katniss Everdeen',
      description: 'This is a description',
      type: queueSeverityEnum.ESI4,
    },
    {
      id: 5,
      name: 'James Bond',
      description: 'This is a description',
      type: queueSeverityEnum.ESI4,
    },
  ]);
  currentTime = toSignal(
    interval(1000).pipe(
      startWith(0), // Start immediately
      map(() =>
        new Date().toLocaleTimeString('nl-BE', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }),
      ),
    ),
  );

  queueItemsViewModel = computed(() =>
    this.queueItems().map((item) => ({
      ...item,
      bgColorClass: this.getQueueItemBgColorClass(item.type),
      borderClass: this.getQueueItemBorderClass(item.type),
    })),
  );

  protected readonly queueSeverityEnum = queueSeverityEnum;

  private getQueueItemBgColorClass(type: QueueSeverity): string {
    switch (type) {
      case queueSeverityEnum.ESI1:
        return 'bg-red-400';
      case queueSeverityEnum.ESI2:
        return 'bg-orange-400';
      case queueSeverityEnum.ESI3:
        return 'bg-yellow-400';
      case queueSeverityEnum.ESI4:
        return 'bg-blue-400';
      default:
        return 'bg-gray-400';
    }
  }

  private getQueueItemBorderClass(type: QueueSeverity): string {
    switch (type) {
      case queueSeverityEnum.ESI1:
        return 'border-red-400';
      case queueSeverityEnum.ESI2:
        return 'border-orange-400';
      case queueSeverityEnum.ESI3:
        return 'border-yellow-400';
      case queueSeverityEnum.ESI4:
        return 'border-blue-400';
      default:
        return 'border-gray-400';
    }
  }
}
