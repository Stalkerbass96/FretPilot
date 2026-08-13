export type OutputSelection = {
  pdf: boolean;
  gp5: boolean;
  ample: boolean;
};

export type ConversionArtifact = {
  id: string;
  kind: "pdf" | "gp5" | "ample_sc_midi";
  name: string;
  size_bytes: number;
  download_url: string;
};

export type ConversionOutput = {
  kind: ConversionArtifact["kind"];
  status: "success" | "unsupported" | "skipped";
  warnings: string[];
  error: string | null;
  artifact_id: string | null;
};

export type ConversionStream = {
  stream_id: string;
  review_required: boolean;
  outputs: ConversionOutput[];
  artifacts: ConversionArtifact[];
};

export type ConversionJob = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  source_filename: string;
  midi_fidelity: number;
  requested_outputs: {
    pdf: boolean;
    gp5: boolean;
    ample_sc_midi: boolean;
  };
  knowledge_snapshot_version: string;
  error: string | null;
  created_at: string;
  completed_at: string | null;
  streams: ConversionStream[];
};

export type KnowledgeEntry = {
  knowledge_id: string;
  domain: string;
  kind: "playing_profile" | "shape_prototype" | string;
  schema_version: string;
  knowledge_version: string;
  status: "candidate" | "evaluated" | "approved" | "deprecated";
  payload: Record<string, unknown>;
  scope: Record<string, string[]>;
  provenance: {
    source_type: string;
    reference: string | null;
    license: string | null;
    notes: string;
    source_ids: string[];
  };
  evaluation: {
    benchmark_version: string | null;
    status: string;
    notes: string;
  };
};

export type KnowledgeSource = {
  source_id: string;
  source_type: string;
  title: string;
  creator: string | null;
  reference: string | null;
  license: string | null;
  allowed_uses: string[];
  notes: string;
};

export type KnowledgeSnapshot = {
  snapshot_version: string;
  schema_version: string;
  status: string;
  sources: KnowledgeSource[];
  entries: KnowledgeEntry[];
};

export type VirtualInstrumentSummary = {
  profile_id: string;
  vendor: string;
  product: string;
  version_family: string;
  maturity: string;
  verification_status: string;
  playable_range: { minimum: number; maximum: number };
  articulation_intents: string[];
};

export type VirtualInstrumentList = {
  snapshot_version: string;
  profiles: VirtualInstrumentSummary[];
};

export type InstrumentAction = {
  kind: string;
  target: number | string | null;
  value: number | string | null;
  timing: string;
  duration_ticks?: number | null;
  notes?: string;
  display_label: string;
  state: string;
  conditions?: Record<string, string | number>;
};

export type InstrumentCapability = {
  intent: string;
  support: string;
  actions: InstrumentAction[];
  fallback_intent?: string | null;
  notes: string;
  playable_min: number | null;
  playable_max: number | null;
  evidence_ids: string[];
};

export type InstrumentControl = {
  capability_id: string;
  category: string;
  support: string;
  actions: InstrumentAction[];
  notes: string;
  evidence_ids: string[];
};

export type VirtualInstrumentProfile = {
  profile_id: string;
  profile_version: string;
  knowledge_version: string;
  vendor: string;
  product: string;
  version_family: string;
  maturity: string;
  verification_status: string;
  instrument_model: string;
  pickup_configuration?: string;
  playable_min: number;
  playable_max: number;
  default_tuning: number[];
  tuning_down_semitones_per_string?: number | null;
  sample_modes: string[];
  supported_formats: string[];
  capabilities: InstrumentCapability[];
  controls: InstrumentControl[];
  velocity_layers: Array<{
    context: string;
    minimum: number;
    maximum: number;
    result: string;
    notes: string;
    evidence_ids: string[];
  }>;
  limitations: string[];
  evidence: Array<{
    evidence_id: string;
    source_type: string;
    reference: string;
    status: string;
    notes: string;
    document_version: string;
    retrieved_on: string;
    verified_on: string;
  }>;
};

const API_BASE = (import.meta.env.VITE_FRETPILOT_API_URL ?? "http://127.0.0.1:8765")
  .replace(/\/$/, "");

async function readJson<T>(response: Response): Promise<T> {
  if (response.ok) return response.json() as Promise<T>;
  let message = `FretPilot API returned ${response.status}.`;
  try {
    const payload = await response.json() as { detail?: string };
    if (payload.detail) message = payload.detail;
  } catch {
    // Keep the status-based fallback when the server returns no JSON body.
  }
  throw new Error(message);
}

export async function createConversionJob(
  file: File,
  fidelityPercent: number,
  outputs: OutputSelection,
): Promise<ConversionJob> {
  const form = new FormData();
  form.append("midi_file", file);
  form.append("midi_fidelity", String(fidelityPercent / 100));
  form.append("include_pdf", String(outputs.pdf));
  form.append("include_gp5", String(outputs.gp5));
  form.append("include_ample_sc_midi", String(outputs.ample));
  return readJson<ConversionJob>(await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    body: form,
  }));
}

export async function getConversionJob(jobId: string): Promise<ConversionJob> {
  return readJson<ConversionJob>(await fetch(`${API_BASE}/api/jobs/${jobId}`));
}

export async function getKnowledgeSnapshot(): Promise<KnowledgeSnapshot> {
  return readJson<KnowledgeSnapshot>(await fetch(`${API_BASE}/api/knowledge`));
}

export async function getVirtualInstrumentList(): Promise<VirtualInstrumentList> {
  return readJson<VirtualInstrumentList>(
    await fetch(`${API_BASE}/api/virtual-instruments`),
  );
}

export async function getVirtualInstrumentProfile(
  profileId: string,
): Promise<VirtualInstrumentProfile> {
  return readJson<VirtualInstrumentProfile>(
    await fetch(`${API_BASE}/api/virtual-instruments/${encodeURIComponent(profileId)}`),
  );
}

export function artifactUrl(path: string): string {
  return path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}
