import type { ConnectionState as StreamConnectionState } from "../lib/task-types";

const labels: Record<StreamConnectionState, string> = {
  connecting: "Connecting to run",
  connected: "Live",
  reconnecting: "Reconnecting",
  closed: "Stream closed",
};

export function ConnectionState({
  state,
}: {
  state: StreamConnectionState;
}) {
  return (
    <span className={`connection-state connection-${state}`} role="status">
      <span aria-hidden="true" />
      {labels[state]}
    </span>
  );
}
