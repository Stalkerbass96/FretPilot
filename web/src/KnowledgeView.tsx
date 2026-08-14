import {
  AlertTriangle,
  BookOpen,
  Cable,
  CheckCircle2,
  ChevronRight,
  Database,
  ExternalLink,
  FlaskConical,
  Layers3,
  LoaderCircle,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  getKnowledgeSnapshot,
  getVirtualInstrumentList,
  getVirtualInstrumentProfile,
  type InstrumentAction,
  type KnowledgeEntry,
  type KnowledgeSnapshot,
  type VirtualInstrumentProfile,
  type VirtualInstrumentSummary,
} from "./api";
import { Badge } from "./components/ui";
import { cn } from "./lib/utils";

type KnowledgeMode = "playing" | "instruments";

const labels: Record<string, string> = {
  adjacent_string_arpeggio: "相邻弦琶音",
  same_string_legato: "同弦连奏",
  hand_position_stability: "把位稳定",
  shape_reuse: "形状复用",
  open_string_usage: "空弦使用",
  wide_interval_position_shift: "大音程换把",
  compact_chord_voicing: "紧凑和弦",
  low_register_bias: "低音区倾向",
  hammer_pull: "Hammer / Pull",
  slide: "Slide",
  bend: "Bend",
  vibrato: "Vibrato",
  palm_mute: "Palm mute",
  let_ring: "Let ring",
  staccato: "Staccato",
  timing_looseness: "时值松弛度",
  velocity_variation: "力度变化",
  note_overlap: "音符重叠",
  accent_strength: "重音强度",
};

const titleCase = (value: string) => value
  .split("_")
  .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
  .join(" ");

function lifecycleTone(status: string): "success" | "warm" | "accent" | "neutral" {
  if (status === "approved" || status === "official") return "success";
  if (status.includes("unverified") || status === "candidate") return "warm";
  if (status === "native") return "accent";
  return "neutral";
}

function statusLabel(status: string) {
  const known: Record<string, string> = {
    approved: "已批准",
    candidate: "候选",
    official: "官方资料",
    plugin_unverified: "尚未插件验证",
    official_documented: "官方文档已录入",
    native: "原生支持",
    approximated: "近似支持",
    unsupported: "不支持",
    baseline: "基线",
    untested: "未测试",
  };
  return known[status] ?? titleCase(status);
}

function PreferenceGroup({
  title,
  values,
}: {
  title: string;
  values: Record<string, number>;
}) {
  return (
    <section className="knowledge-detail-section">
      <h3>{title}</h3>
      <div className="preference-grid">
        {Object.entries(values).map(([key, value]) => (
          <div className="preference-item" key={key}>
            <span>{labels[key] ?? titleCase(key)}</span>
            <strong>{value.toFixed(2)}</strong>
            <i aria-hidden="true"><span style={{ width: `${Math.min(value / 1.7, 1) * 100}%` }} /></i>
          </div>
        ))}
      </div>
    </section>
  );
}

function Provenance({ entry }: { entry: KnowledgeEntry }) {
  return (
    <section className="knowledge-detail-section">
      <h3>来源与评估</h3>
      <div className="provenance-card">
        <div><span>来源类型</span><strong>{titleCase(entry.provenance.source_type)}</strong></div>
        <div><span>参考</span><strong>{entry.provenance.reference ?? "未记录"}</strong></div>
        <div><span>评估</span><strong>{statusLabel(entry.evaluation.status)}</strong></div>
        <div><span>基准版本</span><strong>{entry.evaluation.benchmark_version ?? "尚无"}</strong></div>
      </div>
      {entry.provenance.notes && <p className="knowledge-note">{entry.provenance.notes}</p>}
    </section>
  );
}

function PlayingKnowledgeDetail({ entry }: { entry: KnowledgeEntry }) {
  const payload = entry.payload as {
    label?: string;
    description?: string;
    dimension?: string;
    maturity?: string;
    fingering?: Record<string, number>;
    articulation?: Record<string, number>;
    performance?: Record<string, number>;
    coordinate_system?: string;
    tuning_families?: string[];
    notes?: Array<{
      string_offset: number;
      fret_offset: number;
      interval_semitones: number;
      function: string;
    }>;
  };

  return (
    <article className="knowledge-detail">
      <header className="knowledge-detail__header">
        <div>
          <span className="knowledge-kicker">{entry.kind === "playing_profile" ? "PLAYING PROFILE" : "SHAPE PROTOTYPE"}</span>
          <h2>{payload.label ?? entry.knowledge_id}</h2>
          <p>{payload.description ?? "可复用的吉他指板形状候选。"}</p>
        </div>
        <Badge tone={lifecycleTone(entry.status)}>{statusLabel(entry.status)}</Badge>
      </header>

      <div className="knowledge-meta-strip">
        <div><span>知识 ID</span><code>{entry.knowledge_id}</code></div>
        <div><span>版本</span><code>{entry.knowledge_version}</code></div>
        <div><span>维度</span><strong>{titleCase(payload.dimension ?? entry.kind)}</strong></div>
        <div><span>成熟度</span><strong>{statusLabel(payload.maturity ?? entry.status)}</strong></div>
      </div>

      {payload.fingering && <PreferenceGroup title="指法偏好" values={payload.fingering} />}
      {payload.articulation && <PreferenceGroup title="演奏法偏好" values={payload.articulation} />}
      {payload.performance && <PreferenceGroup title="演奏参数" values={payload.performance} />}

      {payload.notes && (
        <section className="knowledge-detail-section">
          <h3>相对指板坐标</h3>
          <div className="shape-table">
            <div className="shape-table__head"><span>功能</span><span>弦偏移</span><span>品偏移</span><span>音程</span></div>
            {payload.notes.map((note, index) => (
              <div className="shape-table__row" key={`${note.function}-${index}`}>
                <strong>{titleCase(note.function)}</strong>
                <code>{note.string_offset >= 0 ? "+" : ""}{note.string_offset}</code>
                <code>{note.fret_offset >= 0 ? "+" : ""}{note.fret_offset}</code>
                <span>{note.interval_semitones} semitones</span>
              </div>
            ))}
          </div>
          <p className="knowledge-note">
            坐标系：{payload.coordinate_system} · 调弦族：{payload.tuning_families?.join(" / ")}
          </p>
        </section>
      )}

      <section className="knowledge-detail-section">
        <h3>适用范围</h3>
        <div className="scope-list">
          {Object.entries(entry.scope).flatMap(([scope, values]) => values.map((value) => (
            <Badge key={`${scope}-${value}`}>{titleCase(scope)} · {titleCase(value)}</Badge>
          )))}
        </div>
      </section>
      <Provenance entry={entry} />
    </article>
  );
}

function ActionPill({ action }: { action: InstrumentAction }) {
  const midi = typeof action.target === "number" ? `MIDI ${action.target}` : action.target;
  const primary = action.display_label
    ? `${action.display_label} · ${midi}`
    : String(action.value ?? midi ?? titleCase(action.kind));
  return (
    <span className="action-pill">
      <small>{titleCase(action.kind)}</small>
      <strong>{primary}</strong>
      {action.timing && <em>{titleCase(action.timing)}</em>}
    </span>
  );
}

function InstrumentDetail({ profile }: { profile: VirtualInstrumentProfile }) {
  return (
    <article className="knowledge-detail instrument-detail">
      <header className="knowledge-detail__header instrument-title">
        <div>
          <span className="knowledge-kicker">{profile.vendor} · PROFILE {profile.profile_version}</span>
          <h2>{profile.product}</h2>
          <p>{profile.instrument_model} · Bridge pickup sample library</p>
        </div>
        <Badge tone="warm">{statusLabel(profile.verification_status)}</Badge>
      </header>

      <div className="instrument-facts">
        <div><span>产品版本</span><strong>{profile.version_family}</strong></div>
        <div><span>知识快照</span><code>{profile.knowledge_version}</code></div>
        <div><span>演奏音域</span><strong>MIDI {profile.playable_min}–{profile.playable_max}</strong></div>
        <div><span>采样模式</span><strong>{profile.sample_modes.map(titleCase).join(" / ")}</strong></div>
        <div><span>默认调弦</span><code>{profile.default_tuning.join(" · ")}</code></div>
        <div><span>格式</span><strong>{profile.supported_formats.join(" · ")}</strong></div>
      </div>

      <section className="knowledge-detail-section">
        <div className="knowledge-section-heading">
          <div><h3>Articulation 映射</h3><p>厂商音名仅供阅读，渲染器使用原始 MIDI 编号。</p></div>
          <Badge tone="accent">{profile.capabilities.length} 项</Badge>
        </div>
        <div className="capability-list">
          {profile.capabilities.map((capability) => (
            <details className="capability-row" key={capability.intent}>
              <summary>
                <span className="capability-icon"><Cable size={14} /></span>
                <span><strong>{titleCase(capability.intent)}</strong><small>{capability.notes || "官方控制映射"}</small></span>
                <Badge tone={lifecycleTone(capability.support)}>{statusLabel(capability.support)}</Badge>
                <ChevronRight size={15} />
              </summary>
              <div className="capability-body">
                <div className="action-list">{capability.actions.map((action, index) => <ActionPill action={action} key={`${action.kind}-${index}`} />)}</div>
                {(capability.playable_min !== null || capability.playable_max !== null) && (
                  <p>适用音域：MIDI {capability.playable_min ?? profile.playable_min}–{capability.playable_max ?? profile.playable_max}</p>
                )}
                <code>Evidence · {capability.evidence_ids.join(", ")}</code>
              </div>
            </details>
          ))}
        </div>
      </section>

      <section className="knowledge-detail-section">
        <div className="knowledge-section-heading">
          <div><h3>引擎控制族</h3><p>弦、把位、自动连奏、效果与演奏模式。</p></div>
          <Badge>{profile.controls.length} 组</Badge>
        </div>
        <div className="control-grid">
          {profile.controls.map((control) => (
            <details className="control-card" key={control.capability_id}>
              <summary><span>{titleCase(control.category)}</span><strong>{titleCase(control.capability_id)}</strong><ChevronRight size={14} /></summary>
              <div className="action-list">{control.actions.map((action, index) => <ActionPill action={action} key={`${action.kind}-${index}`} />)}</div>
              {control.notes && <p>{control.notes}</p>}
            </details>
          ))}
        </div>
      </section>

      <section className="knowledge-detail-section">
        <h3>力度分层</h3>
        <div className="velocity-layers">
          {profile.velocity_layers.map((layer) => (
            <div key={`${layer.context}-${layer.minimum}`}>
              <code>{layer.minimum}–{layer.maximum}</code>
              <span>{titleCase(layer.result)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="knowledge-detail-section">
        <h3>验证限制</h3>
        <div className="limitation-list">
          {profile.limitations.map((limitation) => <p key={limitation}><AlertTriangle size={14} />{limitation}</p>)}
        </div>
      </section>

      <section className="knowledge-detail-section">
        <h3>证据来源</h3>
        <div className="evidence-list">
          {profile.evidence.map((evidence) => (
            <a href={evidence.reference} target="_blank" rel="noreferrer" key={evidence.evidence_id}>
              <span className="evidence-icon"><BookOpen size={15} /></span>
              <span><strong>{evidence.document_version}</strong><small>{evidence.notes}</small><code>{evidence.evidence_id} · {evidence.retrieved_on}</code></span>
              <Badge tone="success">{statusLabel(evidence.status)}</Badge>
              <ExternalLink size={14} />
            </a>
          ))}
        </div>
      </section>
    </article>
  );
}

function EntryIndex({
  entries,
  selectedId,
  onSelect,
}: {
  entries: KnowledgeEntry[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="knowledge-index-list">
      {entries.map((entry) => {
        const payload = entry.payload as { label?: string; description?: string; dimension?: string };
        return (
          <button className={cn("knowledge-index-item", entry.knowledge_id === selectedId && "knowledge-index-item--active")} onClick={() => onSelect(entry.knowledge_id)} key={entry.knowledge_id}>
            <span className="knowledge-index-icon">{entry.kind === "playing_profile" ? <SlidersHorizontal size={15} /> : <Layers3 size={15} />}</span>
            <span><strong>{payload.label ?? entry.knowledge_id}</strong><small>{titleCase(payload.dimension ?? entry.kind)}</small></span>
            <Badge tone={lifecycleTone(entry.status)}>{statusLabel(entry.status)}</Badge>
          </button>
        );
      })}
    </div>
  );
}

function InstrumentIndex({
  profiles,
  selectedId,
  onSelect,
}: {
  profiles: VirtualInstrumentSummary[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="knowledge-index-list">
      {profiles.map((profile) => (
        <button className={cn("knowledge-index-item", profile.profile_id === selectedId && "knowledge-index-item--active")} onClick={() => onSelect(profile.profile_id)} key={profile.profile_id}>
          <span className="knowledge-index-icon"><Cable size={15} /></span>
          <span><strong>{profile.product}</strong><small>{profile.vendor} · v{profile.version_family}</small></span>
          <Badge tone="warm">未验证</Badge>
        </button>
      ))}
    </div>
  );
}

export function KnowledgeView() {
  const [mode, setMode] = useState<KnowledgeMode>("playing");
  const [snapshot, setSnapshot] = useState<KnowledgeSnapshot | null>(null);
  const [instrumentVersion, setInstrumentVersion] = useState("");
  const [instruments, setInstruments] = useState<VirtualInstrumentSummary[]>([]);
  const [instrumentProfiles, setInstrumentProfiles] = useState<Record<string, VirtualInstrumentProfile>>({});
  const [selectedEntryId, setSelectedEntryId] = useState<string>();
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<string>();
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [nextSnapshot, list] = await Promise.all([
          getKnowledgeSnapshot(),
          getVirtualInstrumentList(),
        ]);
        const profiles = await Promise.all(
          list.profiles.map((profile) => getVirtualInstrumentProfile(profile.profile_id)),
        );
        if (!active) return;
        setSnapshot(nextSnapshot);
        setInstrumentVersion(list.snapshot_version);
        setInstruments(list.profiles);
        setInstrumentProfiles(Object.fromEntries(profiles.map((profile) => [profile.profile_id, profile])));
        setSelectedEntryId(nextSnapshot.entries[0]?.knowledge_id);
        setSelectedInstrumentId(list.profiles[0]?.profile_id);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "知识库暂时无法读取。");
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; };
  }, []);

  const filteredEntries = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return snapshot?.entries ?? [];
    return (snapshot?.entries ?? []).filter((entry) => {
      const payload = entry.payload as { label?: string; description?: string };
      return [entry.knowledge_id, entry.kind, payload.label, payload.description]
        .some((value) => value?.toLowerCase().includes(normalized));
    });
  }, [query, snapshot]);

  const filteredInstruments = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return instruments;
    return instruments.filter((profile) => [profile.profile_id, profile.vendor, profile.product]
      .some((value) => value.toLowerCase().includes(normalized)));
  }, [instruments, query]);

  const selectedEntry = filteredEntries.find((entry) => entry.knowledge_id === selectedEntryId) ?? filteredEntries[0];
  const selectedInstrument = filteredInstruments.find((profile) => profile.profile_id === selectedInstrumentId) ?? filteredInstruments[0];
  const selectedProfile = selectedInstrument ? instrumentProfiles[selectedInstrument.profile_id] : undefined;

  return (
    <div className="page page--knowledge">
      <section className="page-intro knowledge-intro">
        <Badge tone="accent"><Database size={12} /> Review console</Badge>
        <h1>可以被审阅的音乐智能。</h1>
        <p>查看 FretPilot 当前采用的吉他演奏偏好、指板形状，以及针对具体虚拟音源的 MIDI 控制知识。</p>
      </section>

      <section className="knowledge-summary" aria-label="知识库概况">
        <div><span className="summary-icon"><BookOpen size={17} /></span><span><small>演奏知识</small><strong>{snapshot?.entries.length ?? "—"} 个条目</strong></span><code>{snapshot?.snapshot_version ?? "loading"}</code></div>
        <div><span className="summary-icon"><Cable size={17} /></span><span><small>音源适配</small><strong>{instruments.length || "—"} 个 Profile</strong></span><code>{instrumentVersion || "loading"}</code></div>
        <div><span className="summary-icon"><FlaskConical size={17} /></span><span><small>审阅状态</small><strong>人工校验中</strong></span><Badge tone="warm">含候选项</Badge></div>
      </section>

      <div className="knowledge-toolbar">
        <div className="knowledge-tabs" role="tablist" aria-label="知识库类型">
          <button role="tab" aria-selected={mode === "playing"} className={cn(mode === "playing" && "active")} onClick={() => { setMode("playing"); setQuery(""); }}><BookOpen size={15} />演奏知识 <span>{snapshot?.entries.length ?? 0}</span></button>
          <button role="tab" aria-selected={mode === "instruments"} className={cn(mode === "instruments" && "active")} onClick={() => { setMode("instruments"); setQuery(""); }}><Cable size={15} />音源适配 <span>{instruments.length}</span></button>
        </div>
        <label className="knowledge-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索知识条目" aria-label="搜索知识条目" /></label>
      </div>

      {loading && <div className="knowledge-loading"><LoaderCircle className="spin" size={18} />正在读取版本化知识快照…</div>}
      {error && <div className="knowledge-error" role="alert"><AlertTriangle size={16} />{error}</div>}

      {!loading && !error && (
        <section className="knowledge-workbench">
          <aside className="knowledge-index">
            <div className="knowledge-index__header">
              <span>{mode === "playing" ? "KNOWLEDGE ENTRIES" : "INSTRUMENT PROFILES"}</span>
              <strong>{mode === "playing" ? filteredEntries.length : filteredInstruments.length}</strong>
            </div>
            {mode === "playing" ? (
              <EntryIndex entries={filteredEntries} selectedId={selectedEntry?.knowledge_id} onSelect={setSelectedEntryId} />
            ) : (
              <InstrumentIndex profiles={filteredInstruments} selectedId={selectedInstrument?.profile_id} onSelect={setSelectedInstrumentId} />
            )}
          </aside>
          <div className="knowledge-detail-wrap">
            {mode === "playing" && selectedEntry && <PlayingKnowledgeDetail entry={selectedEntry} />}
            {mode === "instruments" && selectedProfile && <InstrumentDetail profile={selectedProfile} />}
            {((mode === "playing" && !selectedEntry) || (mode === "instruments" && !selectedProfile)) && (
              <div className="knowledge-empty"><CheckCircle2 size={22} /><strong>没有匹配条目</strong><span>试试其他搜索条件。</span></div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
