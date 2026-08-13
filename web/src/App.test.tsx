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

  it("loads both knowledge bases for human review", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string) => {
      if (input.endsWith("/api/knowledge")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            snapshot_version: "2026.08.0",
            schema_version: "1",
            status: "approved",
            entries: [{
              knowledge_id: "gk.profile.metal",
              domain: "guitar_playing",
              kind: "playing_profile",
              schema_version: "1",
              knowledge_version: "2026.08.0",
              status: "approved",
              payload: {
                profile_id: "metal",
                label: "Metal",
                dimension: "style",
                description: "Tight low-register guitar language.",
                maturity: "experimental",
                fingering: { hand_position_stability: 1.35 },
                articulation: { palm_mute: 1.6 },
                performance: { timing_looseness: 0.65 },
              },
              scope: { styles: ["metal"] },
              provenance: {
                source_type: "hand_authored",
                reference: "FretPilot hand-authored V0 priors",
                license: null,
                notes: "Soft preference baseline.",
              },
              evaluation: { benchmark_version: "builtin-v0", status: "baseline", notes: "" },
            }],
          }),
        });
      }
      if (input.endsWith("/api/virtual-instruments")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            snapshot_version: "2026.08.0",
            profiles: [{
              profile_id: "ample-metal-eclipse-v4.1",
              vendor: "Ample Sound",
              product: "Ample Metal Eclipse",
              version_family: "4.1",
              maturity: "official_documented",
              verification_status: "plugin_unverified",
              playable_range: { minimum: 36, maximum: 84 },
              articulation_intents: ["sustain", "palm_mute"],
            }],
          }),
        });
      }
      if (input.endsWith("/api/virtual-instruments/ample-metal-eclipse-v4.1")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            profile_id: "ample-metal-eclipse-v4.1",
            profile_version: "1.0.0",
            knowledge_version: "2026.08.0",
            vendor: "Ample Sound",
            product: "Ample Metal Eclipse",
            version_family: "4.1",
            maturity: "official_documented",
            verification_status: "plugin_unverified",
            instrument_model: "ESP Eclipse I",
            playable_min: 36,
            playable_max: 84,
            default_tuning: [40, 45, 50, 55, 59, 64],
            sample_modes: ["mono_di", "stereo_di"],
            supported_formats: ["VST3", "AU"],
            capabilities: [{
              intent: "palm_mute",
              support: "native",
              actions: [{ kind: "keyswitch", target: 26, display_label: "D0", timing: "before_note", state: "latched" }],
              notes: "Lower note velocity produces greater mute depth.",
              playable_min: 36,
              playable_max: 84,
              evidence_ids: ["ame-main-panel-manual"],
            }],
            controls: [],
            velocity_layers: [],
            limitations: ["Plugin playback has not yet been verified."],
            evidence: [{
              evidence_id: "ame-main-panel-manual",
              source_type: "official_manual",
              reference: "https://example.com/manual.pdf",
              status: "official",
              notes: "Control map.",
              document_version: "AME Manual",
              retrieved_on: "2026-08-13",
              verified_on: "",
            }],
          }),
        });
      }
      return Promise.reject(new Error(`Unexpected request: ${input}`));
    }));

    render(<App />);
    await user.click(screen.getByRole("button", { name: "知识库" }));

    expect(await screen.findByRole("heading", { name: "可以被审阅的音乐智能。" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Metal" })).toBeInTheDocument();
    expect(screen.getByText("Palm mute")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /音源适配/ }));
    expect(await screen.findByRole("heading", { name: "Ample Metal Eclipse" })).toBeInTheDocument();
    expect(screen.getByText("D0 · MIDI 26")).toBeInTheDocument();
    expect(screen.getByText("尚未插件验证")).toBeInTheDocument();
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
