/**
 * Minimal test-runner globals required by Vitest's declarations.
 *
 * The pure domain package deliberately does not add DOM or WebWorker libraries
 * to its type environment.
 */
interface AbortSignal {}

declare class Event {}

declare class EventTarget {
  addEventListener(
    type: string,
    listener: (...arguments_: unknown[]) => void,
    options?: unknown,
  ): void;

  removeEventListener(
    type: string,
    listener: (...arguments_: unknown[]) => void,
    options?: unknown,
  ): void;
}

declare class WebSocket {}

declare function clearInterval(handle: unknown): void;

declare function clearTimeout(handle: unknown): void;

declare function queueMicrotask(callback: () => void): void;

declare function setInterval(
  callback: (...arguments_: unknown[]) => void,
  milliseconds?: number,
  ...arguments_: unknown[]
): unknown;

declare function setTimeout(
  callback: (...arguments_: unknown[]) => void,
  milliseconds?: number,
  ...arguments_: unknown[]
): unknown;
