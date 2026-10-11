// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fetchTraeStatus,
  toggleTraeAutopilot,
  triggerTraeUnblock,
  sendTraeMessage,
  triggerTraeNewTask,
  triggerTraeSmartUnblock,
} from "./api";

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function mockFetch(responseBody: unknown = { ok: true }, status = 200) {
  const fetchMock = vi.fn<typeof fetch>(
    async () =>
      new Response(JSON.stringify(responseBody), {
        headers: { "Content-Type": "application/json" },
        status,
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Trae Autopilot API endpoints", () => {
  it("fetchTraeStatus calls /api/trae/status via GET", async () => {
    const fetchMock = mockFetch({
      enabled: true,
      interval_seconds: 5,
      status: "running",
      cdp_connected: true,
      port: 9222,
      last_scan_at: 100,
      last_unblock_at: 100,
      last_action: "none",
      last_error: null,
      projects: {},
    });

    const res = await fetchTraeStatus();
    expect(res.enabled).toBe(true);
    expect(res.status).toBe("running");
    expect(fetchMock).toHaveBeenCalledWith("/api/trae/status", expect.any(Object));
  });

  it("toggleTraeAutopilot sends POST with enabled boolean", async () => {
    const fetchMock = mockFetch({ ok: true, enabled: false, status: "disabled" });
    const res = await toggleTraeAutopilot(false);
    expect(res.ok).toBe(true);
    expect(res.enabled).toBe(false);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/trae/toggle",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ enabled: false }),
      }),
    );
  });

  it("triggerTraeUnblock sends POST with project parameter", async () => {
    const fetchMock = mockFetch({ ok: true, result: "unblocked" });
    const res = await triggerTraeUnblock("my-project");
    expect(res.ok).toBe(true);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/trae/unblock",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ project: "my-project" }),
      }),
    );
  });

  it("sendTraeMessage sends parameterized message and project", async () => {
    const fetchMock = mockFetch({ ok: true, output: "message sent" });
    const res = await sendTraeMessage("Tiếp tục refactor", "my-project");
    expect(res.ok).toBe(true);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/trae/send",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: "Tiếp tục refactor", project: "my-project" }),
      }),
    );
  });

  it("triggerTraeNewTask sends POST to new-task", async () => {
    const fetchMock = mockFetch({ ok: true });
    const res = await triggerTraeNewTask("my-project");
    expect(res.ok).toBe(true);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/trae/new-task",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ project: "my-project" }),
      }),
    );
  });

  it("triggerTraeSmartUnblock sends POST with project and receives smart_prompt", async () => {
    const fetchMock = mockFetch({ ok: true, project: "my-project", smart_prompt: "Smart instructions" });
    const res = await triggerTraeSmartUnblock("my-project");
    expect(res.ok).toBe(true);
    expect(res.smart_prompt).toBe("Smart instructions");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/trae/smart-unblock",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ project: "my-project" }),
      }),
    );
  });
});
