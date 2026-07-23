import {
  capabilitySummary,
  unavailableCapability,
} from "@deepwork/domain";
import {
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StatusPanel } from "@deepwork/ui";

const unknownCapability = capabilitySummary(
  unavailableCapability(
    "unknown",
    "contract-not-verified",
    {
      observedAt: "2026-07-23T00:00:00.000Z",
      adapterVersion: "adapter-disabled",
      contractVersion: "contract-unverified",
      evidenceClass: "documented",
    },
  ),
);

afterEach(cleanup);

describe("StatusPanel", () => {
  it("names loading and error announcements accurately", () => {
    const { rerender } = render(
      <StatusPanel state="loading" title="Loading workspace" />,
    );

    expect(
      screen
        .getByRole("status", { name: "Loading workspace" })
        .getAttribute("aria-live"),
    ).toBe("polite");

    rerender(
      <StatusPanel
        description="Try again after checking the source."
        state="error"
        title="Source could not be loaded"
      />,
    );
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText("Error")).toBeTruthy();
  });

  it("never presents an unknown capability as success or actionable", () => {
    render(
      <StatusPanel
        capability={unknownCapability}
        state="unavailable"
        title="Advanced runtime action"
      />,
    );

    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(
      screen.getByText(
        "Availability is unknown. No request will be attempted.",
      ),
    ).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByText("Available")).toBeNull();
  });

  it("uses a native button for explicitly supplied actions", () => {
    const onAction = vi.fn();
    render(
      <StatusPanel
        action={{ label: "Retry", onAction }}
        state="error"
        title="Connection interrupted"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onAction).toHaveBeenCalledOnce();
  });

  it("renders unsafe and long localized content as text", () => {
    const content =
      '<img src=x onerror="alert(1)"> SehrLangesZusammengesetztesStatuswort';
    render(
      <StatusPanel
        description={content}
        state="success"
        title="Prüfung abgeschlossen"
      />,
    );

    expect(screen.getByText(content)).toBeTruthy();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.getByText("Available")).toBeTruthy();
  });

  it("distinguishes an honest empty state from success", () => {
    render(
      <StatusPanel
        description="The source is healthy and returned no items."
        state="empty"
        title="No tasks yet"
      />,
    );

    expect(screen.getByText("No results")).toBeTruthy();
    expect(screen.queryByText("Available")).toBeNull();
  });
});
