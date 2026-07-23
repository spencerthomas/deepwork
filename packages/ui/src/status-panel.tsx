import type { UnavailableCapabilitySummary, ViewStateKind } from "@deepwork/domain";
import { useId } from "react";

interface StatusPanelBaseProps {
  readonly title: string;
  readonly description?: string;
}

interface StatusPanelAction {
  readonly label: string;
  readonly onAction: () => void;
}

interface LoadingStatusPanelProps extends StatusPanelBaseProps {
  readonly state: "loading";
}

interface EmptyStatusPanelProps extends StatusPanelBaseProps {
  readonly state: "empty";
  readonly action?: StatusPanelAction;
}

interface SuccessStatusPanelProps extends StatusPanelBaseProps {
  readonly state: "success";
  readonly action?: StatusPanelAction;
}

interface ErrorStatusPanelProps extends StatusPanelBaseProps {
  readonly state: "error";
  readonly action?: StatusPanelAction;
}

interface UnavailableStatusPanelProps extends StatusPanelBaseProps {
  readonly state: "unavailable";
  readonly capability: UnavailableCapabilitySummary;
}

export type StatusPanelProps =
  | LoadingStatusPanelProps
  | EmptyStatusPanelProps
  | SuccessStatusPanelProps
  | ErrorStatusPanelProps
  | UnavailableStatusPanelProps;

const STATE_LABELS: Readonly<Record<ViewStateKind, string>> = Object.freeze({
  loading: "Loading",
  empty: "No results",
  success: "Available",
  error: "Error",
  unavailable: "Unavailable",
});

const REASON_LABELS = Object.freeze({
  "contract-not-verified": "Support has not been verified.",
  "not-supported": "This source does not support the capability.",
  "permission-required": "Additional permission is required.",
  "source-unavailable": "The source is currently unavailable.",
  "adapter-disabled": "The adapter is currently disabled.",
} as const);

function capabilityDescription(capability: UnavailableCapabilitySummary): string {
  if (capability.state === "unknown") {
    return "Availability is unknown. No request will be attempted.";
  }

  if (capability.safeReason !== undefined) {
    return REASON_LABELS[capability.safeReason];
  }

  return "This capability is unavailable.";
}

function actionFor(props: StatusPanelProps): StatusPanelAction | undefined {
  if (props.state === "empty" || props.state === "success" || props.state === "error") {
    return props.action;
  }

  return undefined;
}

export function StatusPanel(props: StatusPanelProps) {
  const id = useId();
  const titleId = `${id}-title`;
  const detailId = `${id}-detail`;
  const action = actionFor(props);
  const isUnavailable = props.state === "unavailable";
  const detail = isUnavailable ? capabilityDescription(props.capability) : props.description;
  const role = props.state === "error" ? "alert" : props.state === "loading" ? "status" : undefined;

  return (
    <section
      aria-describedby={detail === undefined ? undefined : detailId}
      aria-labelledby={titleId}
      aria-live={props.state === "loading" ? "polite" : undefined}
      className="dw-status-panel"
      data-state={props.state}
      role={role}
    >
      <div className="dw-status-panel__body">
        <p className="dw-status-panel__label">
          <span aria-hidden="true" className="dw-status-panel__mark">
            {props.state === "success" ? "✓" : "•"}
          </span>
          {STATE_LABELS[props.state]}
        </p>
        <p className="dw-status-panel__title" id={titleId}>
          {props.title}
        </p>
        {detail === undefined ? null : (
          <p className="dw-status-panel__detail" id={detailId}>
            {detail}
          </p>
        )}
      </div>
      {action === undefined ? null : (
        <button className="dw-status-panel__action" onClick={action.onAction} type="button">
          {action.label}
        </button>
      )}
    </section>
  );
}
