import type { WorkReference } from "@deepwork/sdk";
import { WorkLabel } from "@deepwork/ui";
import "@deepwork/ui/status-panel.css";

export function Work(props: WorkReference) {
  return <WorkLabel id={props.id} />;
}
