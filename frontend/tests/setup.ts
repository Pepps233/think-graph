import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";

// ---------------------------------------------------------------------------
// EventSource mock
// ---------------------------------------------------------------------------

class EventSourceMock {
  static latestInstance: EventSourceMock | null = null;

  url: string;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    EventSourceMock.latestInstance = this;
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }

  simulateError() {
    this.onerror?.();
  }
}

vi.stubGlobal("EventSource", EventSourceMock);

afterEach(() => {
  EventSourceMock.latestInstance = null;
  vi.clearAllMocks();
});

export { EventSourceMock };
