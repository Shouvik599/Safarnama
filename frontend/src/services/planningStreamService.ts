import type { FinalItinerary, PlanningEvent } from '../types/itinerary';
import { synthesizeItineraryFromDraft, SAMPLE_HOKURIKU_ITINERARY } from '../data/sampleItinerary';

export interface PlanStreamOptions {
  onEvent: (event: PlanningEvent) => void;
  onComplete: (itinerary: FinalItinerary) => void;
  onError: (errorMsg: string) => void;
  signal?: AbortSignal;
  draftContext?: {
    tripDetails: any;
    destinations: any[];
    preferences: any;
    budget: any;
  };
}

/**
 * Parses raw SSE text chunk into individual PlanningEvent objects
 */
export function parseSSEEvents(chunk: string): PlanningEvent[] {
  const events: PlanningEvent[] = [];
  const blocks = chunk.split(/\n\n+/);

  for (const block of blocks) {
    if (!block.trim()) continue;

    let eventName = 'message';
    let dataStr = '';

    const lines = block.split(/\r?\n/);
    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataStr = line.slice(5).trim();
      }
    }

    if (dataStr) {
      try {
        const parsed = JSON.parse(dataStr);
        events.push({
          event: eventName,
          stage: parsed.stage || eventName,
          message: parsed.message || '',
          data: parsed.data || parsed,
          timestamp: parsed.timestamp || new Date().toISOString(),
        });
      } catch {
        events.push({
          event: eventName,
          stage: eventName,
          message: dataStr,
          data: {},
          timestamp: new Date().toISOString(),
        });
      }
    }
  }

  return events;
}

/**
 * Simulates a realistic SSE stream when the backend is offline or during testing
 */
export function simulatePlanningStream(options: PlanStreamOptions): () => void {
  const { onEvent, onComplete, signal, draftContext } = options;
  let isCancelled = false;

  const cancel = () => {
    isCancelled = true;
  };

  if (signal) {
    signal.addEventListener('abort', cancel);
  }

  const milestones = [
    {
      delay: 300,
      event: {
        event: 'planning_started',
        stage: 'intake',
        message: 'Deconstructing traveler profile, group dynamic, and arrival window.',
      },
    },
    {
      delay: 900,
      event: {
        event: 'intake_completed',
        stage: 'intake',
        message: 'Trip constraints and traveler preferences validated.',
      },
    },
    {
      delay: 1500,
      event: {
        event: 'logistics_completed',
        stage: 'logistics',
        message: 'Mapped transit legs and high-speed rail connections with luggage dispatch buffers.',
      },
    },
    {
      delay: 2200,
      event: {
        event: 'experience_completed',
        stage: 'experience',
        message: 'Curated artisanal guild visits, tea master sessions, and uncrowded morning temple hours.',
      },
    },
    {
      delay: 2900,
      event: {
        event: 'date_optimization_completed',
        stage: 'date_optimizer',
        message: 'Calibrated regional microclimates and seasonal foliage progression indices.',
      },
    },
    {
      delay: 3600,
      event: {
        event: 'budget_calculated',
        stage: 'budget',
        message: 'Allocated budget breakdown across stays, rail passes, and dining.',
      },
    },
    {
      delay: 4200,
      event: {
        event: 'optimization_completed',
        stage: 'optimizer',
        message: 'Eliminated backtrack transit and calibrated unhurried exploration pauses.',
      },
    },
  ];

  milestones.forEach(({ delay, event }) => {
    setTimeout(() => {
      if (isCancelled || signal?.aborted) return;
      onEvent({ ...event, timestamp: new Date().toISOString() });
    }, delay);
  });

  const completeTimeout = setTimeout(() => {
    if (isCancelled || signal?.aborted) return;

    let finalItinerary: FinalItinerary;
    if (draftContext && draftContext.tripDetails) {
      finalItinerary = synthesizeItineraryFromDraft(
        draftContext.tripDetails,
        draftContext.destinations,
        draftContext.preferences,
        draftContext.budget
      );
    } else {
      finalItinerary = SAMPLE_HOKURIKU_ITINERARY;
    }

    onEvent({
      event: 'planning_completed',
      stage: 'complete',
      message: `Final itinerary synthesized successfully: '${finalItinerary.title}'`,
      data: { itinerary: finalItinerary },
      timestamp: new Date().toISOString(),
    });

    onComplete(finalItinerary);
  }, 4800);

  return () => {
    cancel();
    clearTimeout(completeTimeout);
  };
}

/**
 * Initiates the real-time planning stream from the Safarnama API with automatic fallback simulation
 */
export async function startPlanningStream(
  planRequest: any,
  options: PlanStreamOptions
): Promise<() => void> {
  const { onEvent, onComplete, onError, signal } = options;

  try {
    const response = await fetch('/api/v1/plan/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(planRequest),
      signal,
    });

    if (!response.ok || !response.body) {
      // Backend returned non-200 or no stream; fallback to simulation
      console.warn('Backend stream unavailable (status', response.status, '). Falling back to simulation.');
      return simulatePlanningStream(options);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const read = async () => {
      try {
        while (true) {
          if (signal?.aborted) {
            reader.cancel();
            break;
          }

          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = parseSSEEvents(buffer);

          // Retain incomplete event line in buffer if necessary
          const lastDoubleNewline = buffer.lastIndexOf('\n\n');
          if (lastDoubleNewline !== -1) {
            buffer = buffer.slice(lastDoubleNewline + 2);
          }

          for (const ev of events) {
            onEvent(ev);
            if (ev.event === 'planning_completed' && ev.data?.itinerary) {
              onComplete(ev.data.itinerary as FinalItinerary);
            } else if (ev.event === 'error') {
              onError(ev.message || 'Planning halted with an error');
            }
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        console.warn('Stream read exception, switching to simulated completion:', err);
        simulatePlanningStream(options);
      }
    };

    read();

    return () => {
      reader.cancel();
    };
  } catch (err: any) {
    if (err.name === 'AbortError') {
      return () => {};
    }
    // Network failure (e.g. backend server not running) -> Fallback simulation
    return simulatePlanningStream(options);
  }
}
