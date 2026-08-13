import { afterEach, describe, expect, it, vi } from "vitest";
import { createConversionJob, detectGuitarCandidates, getConversionJob } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FretPilot API client", () => {
  it("submits the MIDI and selected engine options as multipart data", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "job-1", status: "queued", streams: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["midi"], "riff.mid", { type: "audio/midi" });

    await createConversionJob(file, 35, { pdf: false, gp5: true, ample: true });

    const [url, request] = fetchMock.mock.calls[0];
    expect(url).toBe("http://127.0.0.1:8765/api/jobs");
    expect(request.method).toBe("POST");
    expect(request.body).toBeInstanceOf(FormData);
    expect(request.body.get("midi_file")).toBe(file);
    expect(request.body.get("midi_fidelity")).toBe("0.35");
    expect(request.body.get("include_pdf")).toBe("false");
    expect(request.body.get("include_gp5")).toBe("true");
    expect(request.body.get("include_ample_sc_midi")).toBe("true");
  });

  it("surfaces API error details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "No likely guitar streams were detected." }),
    }));

    await expect(getConversionJob("bad-job")).rejects.toThrow(
      "No likely guitar streams were detected.",
    );
  });

  it("submits a MIDI for guitar-only preflight", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        source_filename: "arrangement.mid",
        guitar_part_count: 2,
        candidates: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["midi"], "arrangement.mid", { type: "audio/midi" });

    await detectGuitarCandidates(file);

    const [url, request] = fetchMock.mock.calls[0];
    expect(url).toBe("http://127.0.0.1:8765/api/detect");
    expect(request.method).toBe("POST");
    expect(request.body).toBeInstanceOf(FormData);
    expect(request.body.get("midi_file")).toBe(file);
  });
});
