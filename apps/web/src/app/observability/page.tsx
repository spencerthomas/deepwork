import { redirect } from "next/navigation";

/** IA parity with the prototype: /observability lives at /activity here. */
export default function ObservabilityPage() {
  redirect("/activity");
}
