import type { WorkReference } from "@deepwork/sdk";
import { WorkLabel } from "@deepwork/ui";

export function Work(props: WorkReference) {
  return <WorkLabel id={props.id} />;
}
