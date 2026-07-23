import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { ActiveInterrupt, ProposedPlan } from "../../lib/task-types";
import { ApprovalDecisionPanel, decisionButtonLabel } from "./approval-decision-panel";

function render(interrupt: ActiveInterrupt, plan?: ProposedPlan): string {
  return renderToStaticMarkup(
    createElement(ApprovalDecisionPanel, {
      interrupt,
      plan,
      onDecide: () => Promise.resolve(undefined),
      onResolved: () => undefined,
    }),
  );
}

function interruptWith(decisions: ActiveInterrupt["decisions"]): ActiveInterrupt {
  return {
    interruptId: "int-1",
    decisions,
    planRevision: 2,
    title: "Approve the research plan",
    question: "The agent wants to execute the plan below.",
  };
}

const plan: ProposedPlan = {
  evidenceRefs: ["task_1:request"],
  revision: 2,
  steps: ["collect sources", "draft summary", "verify citations", "publish result"],
  title: "Research briefing plan",
};

describe("ApprovalDecisionPanel decision verbs", () => {
  it("renders a button for every advertised verb and nothing else", () => {
    const markup = render(interruptWith(["approve", "reject"]));
    expect(markup).toContain(">Approve</button>");
    expect(markup).toContain(">Reject</button>");
    expect(markup).not.toContain(">Respond</button>");
  });

  it("styles approve as the solid brand action and reject as an outline", () => {
    const markup = render(interruptWith(["approve", "reject"]));
    expect(markup).toContain("bg-brand text-brand-foreground");
    expect(markup).toContain("border border-border bg-card");
  });

  it("disables respond until a comment exists, without disabling other verbs", () => {
    const respondOnly = render(interruptWith(["respond"]));
    expect(respondOnly).toContain(">Respond</button>");
    expect(respondOnly).toContain('disabled=""');

    const approveOnly = render(interruptWith(["approve"]));
    expect(approveOnly).toContain(">Approve</button>");
    expect(approveOnly).not.toContain('disabled=""');
  });

  it("shows an honest message instead of inventing verbs when none are advertised", () => {
    const markup = render(interruptWith([]));
    expect(markup).not.toContain("<button");
    expect(markup).toContain("did not advertise any decision");
  });

  it("renders the question, the first plan steps in order, and the revision badge", () => {
    const markup = render(interruptWith(["approve"]), plan);
    expect(markup).toContain("The agent wants to execute the plan below.");
    expect(markup).toContain("Research briefing plan");
    expect(markup).toContain("1. collect sources");
    expect(markup).toContain("2. draft summary");
    expect(markup).toContain("3. verify citations");
    expect(markup).not.toContain("4. publish result");
    expect(markup).toContain("+1 more step");
    expect(markup).toContain("rev 2");
  });

  it("says so when the API returned no plan instead of showing a placeholder", () => {
    const markup = render(interruptWith(["approve"]));
    expect(markup).toContain("no proposed plan");
  });
});

describe("decisionButtonLabel", () => {
  it("labels idle and in-flight states per verb", () => {
    expect(decisionButtonLabel("approve", false)).toBe("Approve");
    expect(decisionButtonLabel("approve", true)).toBe("Approving…");
    expect(decisionButtonLabel("reject", true)).toBe("Rejecting…");
    expect(decisionButtonLabel("respond", true)).toBe("Sending response…");
  });
});
