import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

const detectionSummary = {
  source_filename: "riff.mid",
  policy_version: "guitar-only-v1",
  total_stream_count: 5,
  guitar_part_count: 2,
  selected_stream_count: 3,
  filtered_count: 2,
  possible_count: 1,
  unlikely_count: 1,
  recommended_stream_ids: ["t0:ch0:p25", "t0:ch0:p28", "t2:ch2:p30"],
  candidates: [{
    group_id: "t0:ch0",
    source_track_index: 0,
    source_track_name: "Guitar Layers",
    display_channel: 1,
    stream_ids: ["t0:ch0:p25", "t0:ch0:p28"],
    fragment_count: 2,
    programs: [
      { program: 25, program_name: "Acoustic Guitar (steel)" },
      { program: 28, program_name: "Electric Guitar (muted)" },
    ],
    note_count: 128,
    guitar_probability: 0.94,
    confidence: 0.96,
    decision: "likely_guitar" as const,
    recommendation: "recommended" as const,
    recommendation_text: "高置信吉他声部，建议生成。",
    reasons: ["轨道名称明确标记为吉他。", "同一轨道和通道包含 2 个 Program 片段，按一个吉他声部展示。"],
  }, {
    group_id: "t2:ch2",
    source_track_index: 2,
    source_track_name: "Short Lead",
    display_channel: 3,
    stream_ids: ["t2:ch2:p30"],
    fragment_count: 1,
    programs: [{ program: 30, program_name: "Distortion Guitar" }],
    note_count: 20,
    guitar_probability: 0.91,
    confidence: 0.93,
    decision: "likely_guitar" as const,
    recommendation: "optional" as const,
    recommendation_text: "高置信吉他，但内容很短；建议试听后决定是否保留。",
    reasons: ["MIDI 音色属于吉他族：Distortion Guitar。"],
  }],
};

describe("FretPilot studio", () => {
  it("accepts a MIDI file and enables generation", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => detectionSummary,
    }));
    render(<App />);
    const file = new File(["midi"], "riff.mid", { type: "audio/midi" });

    expect(screen.getByRole("slider", { name: "MIDI 保真度" })).toBeInTheDocument();

    await user.upload(screen.getByLabelText("选择 MIDI 文件"), file);

    expect(screen.getByText("riff.mid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /开始生成/ })).toBeEnabled();
    expect(await screen.findByRole("heading", { name: "建议保留 2 个吉他声部" })).toBeInTheDocument();
    expect(screen.getByText(/自动过滤 2 个低置信或非吉他流/)).toBeInTheDocument();
    expect(screen.getByText("Guitar Layers")).toBeInTheDocument();
    expect(screen.getByText("94%")).toBeInTheDocument();
  });

  it("rejects a non-MIDI file", () => {
    render(<App />);
    const file = new File(["text"], "notes.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("选择 MIDI 文件"), {
      target: { files: [file] },
    });

    expect(screen.getByRole("alert")).toHaveTextContent("请选择 .mid 或 .midi 文件");
  });

  it("blocks generation when every stream is below the guitar threshold", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...detectionSummary,
        guitar_part_count: 0,
        selected_stream_count: 0,
        filtered_count: 5,
        recommended_stream_ids: [],
        candidates: [],
      }),
    }));
    render(<App />);

    await user.upload(
      screen.getByLabelText("选择 MIDI 文件"),
      new File(["midi"], "keyboard.mid", { type: "audio/midi" }),
    );

    expect(await screen.findByText("没有达到生成阈值的吉他声部")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /开始生成/ })).toBeDisabled();
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
            snapshot_version: "2026.08.2",
            schema_version: "1",
            status: "approved",
            sources: [{
              source_id: "source.book.total_rock_guitar",
              source_type: "user_provided_reference",
              title: "Total Rock Guitar",
              creator: "Troy Stetina",
              reference: "User-provided PDF review copy",
              license: "Copyrighted reference",
              allowed_uses: ["analysis", "derived_abstractions"],
              notes: "Registered once at snapshot level.",
            }],
            entries: [{
              knowledge_id: "gk.profile.metal",
              domain: "guitar_playing",
              kind: "playing_profile",
              schema_version: "1",
              knowledge_version: "2026.08.2",
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
            }, {
              knowledge_id: "gk.execution.rule.clean_rest_dual_hand_muting",
              domain: "guitar_playing",
              kind: "execution_rule",
              schema_version: "1",
              knowledge_version: "2026.08.2",
              status: "candidate",
              payload: {
                label: "休止处双手联合止音",
                description: "休止由左右手共同产生明确静音动作。",
                maturity: "editorial_prior",
                principles: ["左手释放压力，右手压制残响。"],
                hard_constraints: ["休止处不得让前一音自然延续。"],
                soft_preferences: [],
                exceptions: [],
                engine_targets: ["articulation", "performance_plan"],
              },
              scope: { roles: ["riff"] },
              provenance: {
                source_type: "curated_reference",
                reference: null,
                license: null,
                notes: "No source notation embedded.",
                source_ids: ["source.book.total_rock_guitar"],
              },
              evaluation: { benchmark_version: null, status: "untested", notes: "Needs review." },
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

    await user.click(screen.getByRole("button", { name: "筛选：演奏动作" }));
    expect(screen.getByRole("heading", { name: "休止处双手联合止音" })).toBeInTheDocument();
    expect(screen.getByText("休止处不得让前一音自然延续。")).toBeInTheDocument();
    expect(screen.getByText("Total Rock Guitar")).toBeInTheDocument();
    expect(screen.queryByText(/Lesson 1/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /音源适配/ }));
    expect(await screen.findByRole("heading", { name: "Ample Metal Eclipse" })).toBeInTheDocument();
    expect(screen.getByText("D0 · MIDI 26")).toBeInTheDocument();
    expect(screen.getByText("尚未插件验证")).toBeInTheDocument();
  });

  it("runs a conversion and renders downloadable stream artifacts", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: string) => {
      if (input.endsWith("/api/detect")) {
        return Promise.resolve({ ok: true, json: async () => detectionSummary });
      }
      return Promise.resolve({
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
        detection: detectionSummary,
        streams: [{
          stream_id: "t0:ch0:p27",
          group_id: "t0:ch0",
          source_track_name: "Electric Guitar",
          display_channel: 1,
          program_name: "Electric Guitar (clean)",
          note_count: 64,
          guitar_probability: 0.95,
          confidence: 0.97,
          recommendation: "recommended",
          recommendation_text: "高置信吉他声部，建议生成。",
          reasons: ["轨道名称明确标记为吉他。"],
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
      });
    }));
    render(<App />);
    await user.upload(
      screen.getByLabelText("选择 MIDI 文件"),
      new File(["midi"], "riff.mid", { type: "audio/midi" }),
    );

    await user.click(screen.getByRole("button", { name: /开始生成/ }));

    expect(await screen.findByRole("heading", { name: "转换完成" })).toBeInTheDocument();
    expect(screen.getByText("Electric Guitar")).toBeInTheDocument();
    expect(screen.getByText(/吉他概率 95%/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /下载 Guitar Pro 5/ })).toHaveAttribute(
      "href",
      "http://127.0.0.1:8765/api/jobs/job-1/artifacts/artifact-1",
    );
  });
});
