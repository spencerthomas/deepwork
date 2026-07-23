import type { WorkId } from "@deepwork/domain";

export function WorkLabel(props: { id: WorkId }) {
  return <span>{props.id}</span>;
}
