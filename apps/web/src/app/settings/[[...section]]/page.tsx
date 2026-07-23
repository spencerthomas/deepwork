import { SettingsShell } from "@/components/settings/settings-shell";
import { resolveSettingsSection } from "@/lib/settings-sections";

export const metadata = {
  title: "Settings — Deep Work",
};

/** /settings and /settings/{section}; unknown sections fall back to appearance. */
export default async function SettingsPage({
  params,
}: {
  params: Promise<{ section?: string[] }>;
}) {
  const { section } = await params;
  return <SettingsShell section={resolveSettingsSection(section)} />;
}
