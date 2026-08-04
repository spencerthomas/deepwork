import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { ActiveInterrupt } from "../../lib/task-types";
import { orderedApprovalIdentity, OrderedApprovalBatch } from "./ordered-approval-batch";

describe("OrderedApprovalBatch", () => {
  it("renders repeated action names as distinct ordered review rows", () => {
    const interrupt: ActiveInterrupt = {
      interruptId: "interrupt-1",
      version: "interrupt-1:1",
      title: "Review the execution plan",
      question: "Review every action in order.",
      decisions: ["approve", "reject"],
      actionRequests: [
        { name: "execute_plan_step", args: { position: 1, text: "Inspect" } },
        { name: "execute_plan_step", args: { position: 2, text: "Verify" } },
      ],
      reviewConfigs: [
        { actionName: "execute_plan_step", allowedDecisions: ["approve", "edit"] },
        { actionName: "execute_plan_step", allowedDecisions: ["approve", "edit", "reject"] },
      ],
    };
    const markup = renderToStaticMarkup(
      createElement(OrderedApprovalBatch, {
        interrupt,
        onSubmit: async () => undefined,
      }),
    );
    expect(markup.match(/execute_plan_step/g)).toHaveLength(2);
    expect(markup).toContain("Inspect");
    expect(markup).toContain("Verify");
    expect(markup).not.toContain("Approve all 2");
    expect(markup).toContain("Batch summary: 0 approve");
    expect(markup).toContain("2 not reviewed");
    expect(markup).toContain('disabled=""');
  });

  it("changes component identity only when the reviewed interrupt version changes", () => {
    const base: ActiveInterrupt = {
      interruptId: "interrupt-1",
      version: "1",
      title: "Review",
      question: "Proceed?",
      decisions: ["approve"],
    };

    expect(orderedApprovalIdentity(base)).toBe(orderedApprovalIdentity({ ...base }));
    expect(orderedApprovalIdentity({ ...base, version: "2" })).not.toBe(
      orderedApprovalIdentity(base),
    );
    expect(orderedApprovalIdentity({ ...base, interruptId: "interrupt-2" })).not.toBe(
      orderedApprovalIdentity(base),
    );
  });
});
