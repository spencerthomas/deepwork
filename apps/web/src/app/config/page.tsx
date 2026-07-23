import { redirect } from "next/navigation";

/** IA parity with the prototype: /config lives at /settings here. */
export default function ConfigPage() {
  redirect("/settings");
}
