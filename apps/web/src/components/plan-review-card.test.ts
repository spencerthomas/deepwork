import { describe, expect, it, vi } from "vitest";

import { focusAfterRender } from "./plan-review-card";

describe("plan review focus handoff", () => {
  it("waits for the editor render before focusing Step 1 after keyboard activation", () => {
    const focus = vi.fn();
    let renderCallback: (() => void) | undefined;

    focusAfterRender(
      () => ({ focus }),
      (callback) => {
        renderCallback = callback;
      },
    );

    expect(focus).not.toHaveBeenCalled();
    renderCallback?.();
    expect(focus).toHaveBeenCalledOnce();
  });

  it("uses the same delayed handoff for the stable review status after save or cancel", () => {
    const editorFocus = vi.fn();
    const reviewFocus = vi.fn();
    const scheduled: Array<() => void> = [];
    const schedule = (callback: () => void) => scheduled.push(callback);

    focusAfterRender(() => ({ focus: editorFocus }), schedule);
    focusAfterRender(() => ({ focus: reviewFocus }), schedule);
    scheduled.forEach((callback) => callback());

    expect(editorFocus).toHaveBeenCalledOnce();
    expect(reviewFocus).toHaveBeenCalledOnce();
  });
});
