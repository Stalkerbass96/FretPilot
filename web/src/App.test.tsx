import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FretPilot studio", () => {
  it("accepts a MIDI file and enables generation", async () => {
    const user = userEvent.setup();
    render(<App />);
    const file = new File(["midi"], "riff.mid", { type: "audio/midi" });

    expect(screen.getByRole("slider", { name: "MIDI 保真度" })).toBeInTheDocument();

    await user.upload(screen.getByLabelText("选择 MIDI 文件"), file);

    expect(screen.getByText("riff.mid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /开始生成/ })).toBeEnabled();
  });

  it("rejects a non-MIDI file", () => {
    render(<App />);
    const file = new File(["text"], "notes.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("选择 MIDI 文件"), {
      target: { files: [file] },
    });

    expect(screen.getByRole("alert")).toHaveTextContent("请选择 .mid 或 .midi 文件");
  });

  it("exposes the design system from primary navigation", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "设计系统" }));

    expect(screen.getByRole("heading", { name: "克制、清晰、为音乐留白。" })).toBeInTheDocument();
    expect(screen.getByText("Quiet Studio · 0.1")).toBeInTheDocument();
  });

  it("runs a conversion and renders downloadable stream artifacts", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "job-1",
        status: "completed",
        progress: 100,
        source_filename: "riff.mid",
        midi_fidelity: 0.35,
        requested_outputs: { pdf: true, gp5: true, ample_sc_midi: true },
        error: null,
        created_at: "2026-08-13T00:00:00Z",
        completed_at: "2026-08-13T00:00:01Z",
        streams: [{
          stream_id: "t0:ch0:p27",
          review_required: true,
          outputs: [],
          artifacts: [{
            id: "artifact-1",
            kind: "gp5",
            name: "guitar.gp5",
            size_bytes: 2048,
            download_url: "/api/jobs/job-1/artifacts/artifact-1",
          }],
        }],
      }),
    }));
    render(<App />);
    await user.upload(
      screen.getByLabelText("选择 MIDI 文件"),
      new File(["midi"], "riff.mid", { type: "audio/midi" }),
    );

    await user.click(screen.getByRole("button", { name: /开始生成/ }));

    expect(await screen.findByRole("heading", { name: "转换完成" })).toBeInTheDocument();
    expect(screen.getByText("t0:ch0:p27")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /下载 Guitar Pro 5/ })).toHaveAttribute(
      "href",
      "http://127.0.0.1:8765/api/jobs/job-1/artifacts/artifact-1",
    );
  });
});
