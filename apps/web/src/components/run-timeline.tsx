import { getEventText } from "../lib/task-normalizers";
import type { TaskEvent } from "../lib/task-types";

const eventLabels: Record<TaskEvent["name"], string> = {
  "task.created": "Task created",
  "run.started": "Run started",
  "content.delta": "Agent update",
  "plan.proposed": "Plan proposed",
  "interrupt.requested": "Approval requested",
  "decision.recorded": "Decision recorded",
  "run.completed": "Run completed",
};

function EventBody({ event }: { event: TaskEvent }) {
  const text = getEventText(event);
  const steps = Array.isArray(event.data.steps)
    ? event.data.steps.filter((step): step is string => typeof step === "string" && step !== "")
    : [];

  if (event.name === "decision.recorded") {
    const decision =
      event.data.decision === "approve"
        ? "Approved"
        : event.data.decision === "reject"
          ? "Rejected"
          : undefined;
    const comment = typeof event.data.comment === "string" ? event.data.comment : undefined;
    return (
      <>
        <p>{decision ? `${decision} by a reviewer.` : "Malformed decision record ignored."}</p>
        {comment ? <blockquote>{comment}</blockquote> : null}
      </>
    );
  }

  return (
    <>
      {text ? <p>{text}</p> : null}
      {steps.length > 0 ? (
        <ul className="plan-steps">
          {steps.map((step, index) => (
            <li key={`${index}:${step}`}>{step}</li>
          ))}
        </ul>
      ) : null}
    </>
  );
}

export function RunTimeline({ events }: { events: readonly TaskEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="timeline-empty" role="status">
        <span className="timeline-pulse" aria-hidden="true" />
        <div>
          <strong>Waiting for the first event</strong>
          <p>The run stream is connected as soon as the task is selected.</p>
        </div>
      </div>
    );
  }

  return (
    <ol className="timeline" aria-label="Run events" aria-live="polite">
      {events.map((event, index) => (
        <li className={`timeline-event event-${event.name.replace(".", "-")}`} key={event.id}>
          <div className="timeline-marker" aria-hidden="true">
            {index + 1}
          </div>
          <article>
            <div className="timeline-event-heading">
              <h3>{eventLabels[event.name]}</h3>
              <code>{event.id}</code>
            </div>
            <EventBody event={event} />
          </article>
        </li>
      ))}
    </ol>
  );
}
