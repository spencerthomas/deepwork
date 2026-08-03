import { describe, expect, it } from "vitest";

import { appendUniqueTaskEvent } from "./task-event-index";
import type { TaskEvent } from "./task-types";

function event(id: string): TaskEvent {
  return { id, name: "content.delta", data: { text: `Update ${id}` } };
}

describe("appendUniqueTaskEvent", () => {
  it("appends unseen ids and rejects replay without scanning retained events", () => {
    const retained = [event("1"), event("2")];
    const seen = new Set(retained.map((item) => item.id));

    const appended = appendUniqueTaskEvent(retained, seen, event("3"));

    expect(appended?.map((item) => item.id)).toEqual(["1", "2", "3"]);
    expect(appendUniqueTaskEvent(appended ?? retained, seen, event("2"))).toBeUndefined();
    expect(seen).toEqual(new Set(["1", "2", "3"]));
    expect(retained.map((item) => item.id)).toEqual(["1", "2"]);
  });
});
