import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileAudio2,
  FileMusic,
  FolderClock,
  Gauge,
  Guitar,
  LayoutDashboard,
  LibraryBig,
  Menu,
  Music2,
  Plus,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import {
  type ChangeEvent,
  type DragEvent,
  type ReactNode,
  useRef,
  useState,
} from "react";
import { Badge, Button, SectionHeader, Slider, Switch } from "./components/ui";
import { cn } from "./lib/utils";

type View = "studio" | "projects" | "system";
type OutputKey = "pdf" | "gp5" | "ample";

const recentProjects = [
  {
    name: "Story of Despair",
    meta: "Lead Electric Guitar · 58 小节",
    when: "刚刚",
    progress: "需要审阅",
    tone: "warm" as const,
    formats: ["PDF", "GP5", "MIDI"],
  },
  {
    name: "Message in a Bottle",
    meta: "Electric Guitar (clean) · 181 小节",
    when: "今天",
    progress: "已完成",
    tone: "success" as const,
    formats: ["PDF", "GP5", "MIDI"],
  },
];

const outputOptions: Array<{
  key: OutputKey;
  title: string;
  description: string;
  icon: typeof FileMusic;
}> = [
  {
    key: "pdf",
    title: "PDF / TAB",
    description: "适合快速审阅与分享",
    icon: FileMusic,
  },
  {
    key: "gp5",
    title: "Guitar Pro 5",
    description: "继续编辑与精修",
    icon: Guitar,
  },
  {
    key: "ample",
    title: "Ample MIDI",
    description: "带演奏法的性能 MIDI",
    icon: FileAudio2,
  },
];

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
      <span />
      <span />
      <i />
    </span>
  );
}

function NavItem({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className={cn("nav-item", active && "nav-item--active")}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function Sidebar({ view, onView }: { view: View; onView: (view: View) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <BrandMark />
        <div>
          <strong>FretPilot</strong>
          <span>Guitar intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="主导航">
        <p className="nav-label">工作空间</p>
        <NavItem
          active={view === "studio"}
          icon={<LayoutDashboard size={17} />}
          label="转换工作台"
          onClick={() => onView("studio")}
        />
        <NavItem
          active={view === "projects"}
          icon={<LibraryBig size={17} />}
          label="项目资料库"
          onClick={() => onView("projects")}
        />
        <p className="nav-label nav-label--spaced">系统</p>
        <NavItem
          active={view === "system"}
          icon={<SlidersHorizontal size={17} />}
          label="设计系统"
          onClick={() => onView("system")}
        />
      </nav>

      <div className="engine-status">
        <div className="engine-status__icon">
          <ShieldCheck size={16} />
        </div>
        <div>
          <span>本地引擎</span>
          <strong><i /> 就绪</strong>
        </div>
        <ChevronRight size={15} />
      </div>
    </aside>
  );
}

function MobileHeader({ onMenu }: { onMenu: () => void }) {
  return (
    <div className="mobile-header">
      <button className="mobile-menu" onClick={onMenu} aria-label="打开导航">
        <Menu size={19} />
      </button>
      <div className="brand brand--mobile"><BrandMark /><strong>FretPilot</strong></div>
      <span className="engine-dot" aria-label="引擎就绪" />
    </div>
  );
}

function Topbar({ view }: { view: View }) {
  const titles: Record<View, string> = {
    studio: "转换工作台",
    projects: "项目资料库",
    system: "设计系统",
  };
  return (
    <header className="topbar">
      <div className="breadcrumbs">
        <span>FretPilot</span>
        <ChevronRight size={13} />
        <strong>{titles[view]}</strong>
      </div>
      <div className="topbar-actions">
        <button className="help-button"><CircleHelp size={15} /> 使用指南</button>
        <span className="topbar-rule" />
        <button className="avatar" aria-label="用户菜单">SW</button>
      </div>
    </header>
  );
}

function UploadArea({ file, onFile }: { file: File | null; onFile: (file: File | null) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  const acceptFile = (candidate?: File) => {
    if (!candidate) return;
    if (!candidate.name.toLowerCase().match(/\.(mid|midi)$/)) {
      setError("请选择 .mid 或 .midi 文件");
      return;
    }
    setError("");
    onFile(candidate);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files[0]);
  };

  const onInput = (event: ChangeEvent<HTMLInputElement>) => {
    acceptFile(event.target.files?.[0]);
  };

  if (file) {
    return (
      <div className="selected-file" aria-live="polite">
        <div className="selected-file__icon"><FileMusic size={22} /></div>
        <div className="selected-file__copy">
          <strong>{file.name}</strong>
          <span>{Math.max(file.size / 1024, 1).toFixed(1)} KB · MIDI 文件</span>
        </div>
        <Badge tone="success"><Check size={12} /> 已就绪</Badge>
        <Button
          variant="ghost"
          size="icon"
          aria-label="移除文件"
          onClick={() => onFile(null)}
        >
          <X size={17} />
        </Button>
      </div>
    );
  }

  return (
    <>
      <div
        className={cn("upload-area", dragging && "upload-area--dragging")}
        onDragEnter={() => setDragging(true)}
        onDragLeave={() => setDragging(false)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
      >
        <div className="staff-preview" aria-hidden="true">
          {[0, 1, 2, 3, 4].map((line) => <span key={line} />)}
          <i className="note note--one" />
          <i className="note note--two" />
          <i className="note note--three" />
        </div>
        <div className="upload-icon"><UploadCloud size={23} /></div>
        <h3>把 MIDI 放到这里</h3>
        <p>拖放文件，或从电脑中选择</p>
        <Button variant="secondary" onClick={() => inputRef.current?.click()}>
          <Plus size={15} /> 选择 MIDI
        </Button>
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept=".mid,.midi,audio/midi,audio/x-midi"
          onChange={onInput}
          aria-label="选择 MIDI 文件"
        />
      </div>
      {error && <p className="field-error" role="alert">{error}</p>}
    </>
  );
}

function FidelityControl({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return (
    <div className="preference-block">
      <div className="preference-heading">
        <div>
          <span>音符取向</span>
          <p>控制修正力度与原始 MIDI 保真度</p>
        </div>
        <Badge tone="accent">推荐 {value}%</Badge>
      </div>
      <Slider value={value} onValueChange={onChange} label="MIDI 保真度" />
      <div className="slider-labels">
        <span>更合理、可演奏</span>
        <span>更忠于原始 MIDI</span>
      </div>
    </div>
  );
}

function OutputSelector({
  outputs,
  onToggle,
}: {
  outputs: Record<OutputKey, boolean>;
  onToggle: (key: OutputKey, enabled: boolean) => void;
}) {
  return (
    <div className="output-list">
      {outputOptions.map(({ key, title, description, icon: Icon }) => (
        <div className="output-row" key={key}>
          <div className="output-row__icon"><Icon size={17} /></div>
          <div className="output-row__copy">
            <strong>{title}</strong>
            <span>{description}</span>
          </div>
          <Switch
            checked={outputs[key]}
            onCheckedChange={(enabled) => onToggle(key, enabled)}
            label={`生成 ${title}`}
          />
        </div>
      ))}
    </div>
  );
}

function StudioView() {
  const [file, setFile] = useState<File | null>(null);
  const [fidelity, setFidelity] = useState(35);
  const [outputs, setOutputs] = useState<Record<OutputKey, boolean>>({
    pdf: true,
    gp5: true,
    ample: true,
  });
  const [queued, setQueued] = useState(false);

  const selectedOutputCount = Object.values(outputs).filter(Boolean).length;

  return (
    <div className="page page--studio">
      <section className="hero">
        <Badge tone="accent"><Sparkles size={12} /> Guitar-aware conversion</Badge>
        <h1>让 MIDI 成为真正<br />可以弹奏的吉他谱。</h1>
        <p>识别吉他声部，修正不合理音符，并生成清晰的 TAB、GP5 与虚拟吉他演奏 MIDI。</p>
      </section>

      <section className="studio-grid" aria-label="新建转换">
        <article className="panel panel--upload">
          <div className="panel-heading">
            <div className="step-number">01</div>
            <div><h2>选择音乐</h2><p>支持 Standard MIDI File</p></div>
          </div>
          <UploadArea file={file} onFile={(nextFile) => { setFile(nextFile); setQueued(false); }} />
          <div className="privacy-note"><ShieldCheck size={14} /> 文件仅在本地处理，不会上传到云端</div>
        </article>

        <article className="panel panel--settings">
          <div className="panel-heading">
            <div className="step-number">02</div>
            <div><h2>设置输出</h2><p>默认值已偏向合理演奏</p></div>
            <Button variant="ghost" size="icon" aria-label="高级设置"><Settings2 size={17} /></Button>
          </div>
          <FidelityControl value={fidelity} onChange={setFidelity} />
          <div className="panel-divider" />
          <OutputSelector
            outputs={outputs}
            onToggle={(key, enabled) => setOutputs((current) => ({ ...current, [key]: enabled }))}
          />
          <Button
            className="generate-button"
            disabled={!file || selectedOutputCount === 0}
            onClick={() => setQueued(true)}
          >
            {queued ? <><Check size={16} /> 已加入本地处理队列</> : <><Sparkles size={16} /> 开始生成 <ArrowRight size={16} /></>}
          </Button>
          <p className="generate-hint">
            {file ? `将生成 ${selectedOutputCount} 种输出格式` : "选择 MIDI 后即可开始"}
          </p>
        </article>
      </section>

      <section className="recent-section">
        <SectionHeader
          eyebrow="Recent work"
          title="最近项目"
          action={<Button variant="ghost" size="small">查看全部 <ArrowRight size={14} /></Button>}
        />
        <div className="project-table">
          {recentProjects.map((project) => (
            <button className="project-row" key={project.name}>
              <span className="project-art"><Music2 size={18} /></span>
              <span className="project-copy"><strong>{project.name}</strong><small>{project.meta}</small></span>
              <span className="format-list">{project.formats.map((format) => <Badge key={format}>{format}</Badge>)}</span>
              <Badge tone={project.tone}>{project.progress}</Badge>
              <span className="project-time"><Clock3 size={13} /> {project.when}</span>
              <ChevronRight className="project-arrow" size={16} />
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function ProjectsView() {
  return (
    <div className="page">
      <section className="page-intro">
        <Badge tone="neutral"><FolderClock size={12} /> Local library</Badge>
        <h1>项目资料库</h1>
        <p>集中查看每次转换的源文件、输出格式与需要人工审阅的位置。</p>
      </section>
      <div className="library-toolbar">
        <div className="library-stats"><strong>2</strong><span>个项目</span></div>
        <Button><Plus size={15} /> 新建转换</Button>
      </div>
      <div className="project-cards">
        {recentProjects.map((project, index) => (
          <article className="project-card" key={project.name}>
            <div className="project-card__art">
              <BrandMark />
              <span>0{index + 1}</span>
            </div>
            <div className="project-card__body">
              <div><Badge tone={project.tone}>{project.progress}</Badge><span>{project.when}</span></div>
              <h2>{project.name}</h2>
              <p>{project.meta}</p>
              <div className="project-card__footer">
                <span>{project.formats.map((format) => <Badge key={format}>{format}</Badge>)}</span>
                <Button variant="ghost" size="icon" aria-label={`打开 ${project.name}`}><ArrowRight size={16} /></Button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function SystemView() {
  const [demoSwitch, setDemoSwitch] = useState(true);
  const colors = [
    ["Canvas", "#F7F8F5", "var(--canvas)"],
    ["Surface", "#FFFFFF", "var(--surface)"],
    ["Ink", "#17211D", "var(--ink)"],
    ["Pine", "#236B55", "var(--accent)"],
    ["Sage", "#DDEBE4", "var(--accent-soft)"],
    ["Amber", "#B86A24", "var(--warm)"],
  ];
  return (
    <div className="page">
      <section className="page-intro">
        <Badge tone="accent"><Gauge size={12} /> Quiet Studio · 0.1</Badge>
        <h1>克制、清晰、为音乐留白。</h1>
        <p>以语义 token 约束颜色、圆角、间距和交互，让新功能自然延续同一种视觉语言。</p>
      </section>

      <section className="system-section">
        <SectionHeader eyebrow="Foundation 01" title="颜色与表面" />
        <div className="color-grid">
          {colors.map(([name, value, color]) => (
            <div className="color-chip" key={name}>
              <span style={{ background: color }} />
              <strong>{name}</strong><small>{value}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="system-section">
        <SectionHeader eyebrow="Foundation 02" title="字体层级" />
        <div className="type-specimen">
          <div><span>Display / 48</span><h2>Guitar intelligence.</h2></div>
          <div><span>Heading / 24</span><h3>清晰，而不喧闹。</h3></div>
          <div><span>Body / 15</span><p>复杂的音乐处理应该藏在背后，界面只呈现当前真正需要作出的决定。</p></div>
          <div><span>Mono / 12</span><code>t0:ch4:p27 · MIDI_FIDELITY 0.35</code></div>
        </div>
      </section>

      <section className="system-section">
        <SectionHeader eyebrow="Components" title="交互组件" />
        <div className="component-stage">
          <div className="component-group"><span>BUTTONS</span><div><Button>主要操作</Button><Button variant="secondary">次要操作</Button><Button variant="ghost">安静操作</Button></div></div>
          <div className="component-group"><span>STATUS</span><div><Badge tone="success">已完成</Badge><Badge tone="warm">需要审阅</Badge><Badge tone="accent">推荐设置</Badge></div></div>
          <div className="component-group"><span>CONTROL</span><div><Switch checked={demoSwitch} onCheckedChange={setDemoSwitch} label="演示开关" /><small>{demoSwitch ? "启用" : "停用"}</small></div></div>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<View>("studio");
  const [mobileNav, setMobileNav] = useState(false);

  return (
    <div className="app-shell">
      {mobileNav && (
        <div className="mobile-drawer mobile-drawer--open">
          <button className="drawer-backdrop" onClick={() => setMobileNav(false)} aria-label="关闭导航" />
          <div className="drawer-panel">
            <Sidebar
              view={view}
              onView={(nextView) => { setView(nextView); setMobileNav(false); }}
            />
          </div>
        </div>
      )}
      <Sidebar view={view} onView={setView} />
      <main className="main-column">
        <MobileHeader onMenu={() => setMobileNav(true)} />
        <Topbar view={view} />
        {view === "studio" && <StudioView />}
        {view === "projects" && <ProjectsView />}
        {view === "system" && <SystemView />}
      </main>
    </div>
  );
}
