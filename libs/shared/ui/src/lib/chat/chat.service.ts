import {
  HttpClient,
  HttpDownloadProgressEvent,
  HttpEvent,
  HttpEventType,
} from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import {
  catchError,
  concatMap,
  filter,
  map,
  scan,
  takeWhile,
} from 'rxjs/operators';
import {
  StreamedChatResponsePart,
  StreamedResponsePartTypeEnum,
} from './chat.types';

@Injectable({ providedIn: 'root' })
export class ChatService {
  readonly #http = inject(HttpClient);
  readonly #apiEndpoint = 'http://localhost:8000/api';

  sendMessage(query: string): Observable<StreamedChatResponsePart> {
    return this.#http
      .post(
        `${this.#apiEndpoint}/chat_stream`,
        { query },
        { responseType: 'text', observe: 'events', reportProgress: true }
      )
      .pipe(
        filter(this.isDownloadProgressEvent),
        map((event) => this.extractPartialTextFromEvent(event)),
        scan(
          (accScanState, currentCumulativeText) => {
            const { newLines, nextProcessedLength } =
              this.calculateScanAccumulator(
                accScanState,
                currentCumulativeText
              );
            return {
              linesToProcess: newLines,
              processedLength: nextProcessedLength,
            };
          },
          { linesToProcess: [] as string[], processedLength: 0 }
        ),
        concatMap((scanResult) => scanResult.linesToProcess),
        map((line) => this.parseJsonTextLine(line)),
        takeWhile(
          (response) => response.type !== StreamedResponsePartTypeEnum.Done,
          true
        ),
        catchError((error) => {
          console.error('Error in HTTP stream:', error);
          return new Observable<StreamedChatResponsePart>((observer) => {
            observer.next({
              type: StreamedResponsePartTypeEnum.Error,
              error: error.message ?? 'Unknown stream error',
            });
            observer.complete();
          });
        })
      );
  }

  private isDownloadProgressEvent(
    event: HttpEvent<string>
  ): event is HttpDownloadProgressEvent {
    return event.type === HttpEventType.DownloadProgress;
  }

  private extractPartialTextFromEvent(
    event: HttpDownloadProgressEvent
  ): string {
    return String(event.partialText ?? '');
  }

  private calculateScanAccumulator(
    accumulator: { processedLength: number },
    currentText: string
  ): { newLines: string[]; nextProcessedLength: number } {
    const newTextSegment = currentText.substring(accumulator.processedLength);
    const lines = newTextSegment
      .split('\n')
      .filter((line: string) => line.trim() !== '');
    return {
      newLines: lines,
      nextProcessedLength: currentText.length,
    };
  }

  private parseJsonTextLine(line: string): StreamedChatResponsePart {
    try {
      return JSON.parse(line);
    } catch (e) {
      console.error('Error parsing JSON line:', e, 'Line:', line);
      return {
        type: StreamedResponsePartTypeEnum.Error,
        error: 'Error parsing JSON from stream',
      };
    }
  }
}
