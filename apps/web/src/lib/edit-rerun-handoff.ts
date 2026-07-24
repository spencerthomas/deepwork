/**
 * Transient, in-memory handoff for "Edit & re-run": carries a task's prompt to
 * the composer across a single client-side navigation.
 *
 * The prompt is deliberately NOT placed in the URL. Prompts can contain private
 * research or repository context (AGENTS.md: treat such content as untrusted and
 * enforce URL boundaries), and a query string would persist that content in
 * browser history, the referrer, and any URL-observing infrastructure. Holding
 * it in module state keeps it inside the authorized client session and clears it
 * on the next full load, so a reload starts from a blank composer.
 */
let pendingPrompt: string | null = null;

export function setEditRerunPrompt(prompt: string): void {
  pendingPrompt = prompt;
}

/** Return the pending prompt once, clearing it so it is used at most one time. */
export function consumeEditRerunPrompt(): string | null {
  const prompt = pendingPrompt;
  pendingPrompt = null;
  return prompt;
}
