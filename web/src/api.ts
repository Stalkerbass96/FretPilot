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
  error: string | null;
  created_at: string;
  completed_at: string | null;
  streams: ConversionStream[];
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

export function artifactUrl(path: string): string {
  return path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}
