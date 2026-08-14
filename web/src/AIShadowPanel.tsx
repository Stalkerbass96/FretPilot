import { BrainCircuit, Check, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import {
  createAIShadowReport,
  getAIStatus,
  type AIShadowReport,
  type AIStatus,
} from "./api";
import { Badge, Button } from "./components/ui";

export function AIShadowPanel({
  file,
  fidelity,
  streamId,
}: {
  file: File | null;
  fidelity: number;
  streamId?: string;
}) {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [consent, setConsent] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState<AIShadowReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void getAIStatus()
      .then((nextStatus) => {
        if (active) setStatus(nextStatus);
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "无法读取 AI 配置");
      })
      .finally(() => {
        if (active) setLoadingStatus(false);
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    setReport(null);
    setError("");
  }, [file, fidelity, streamId]);

  const analyze = async () => {
    if (!file || !consent || !status?.configured || analyzing) return;
    setAnalyzing(true);
    setError("");
    try {
      setReport(await createAIShadowReport(file, fidelity, streamId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "AI 建议生成失败");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <section className="ai-shadow-panel" aria-label="AI Shadow 建议">
      <div className="ai-shadow-panel__heading">
        <div className="ai-shadow-panel__icon"><BrainCircuit size={17} /></div>
        <div>
          <strong>AI 智能增强</strong>
          <span>Shadow 模式 · 只给建议，不修改 MIDI</span>
        </div>
        {loadingStatus
          ? <LoaderCircle className="spin" size={15} />
          : <Badge tone={status?.configured ? "success" : "neutral"}>
              {status?.configured ? "已配置" : "未配置"}
            </Badge>}
      </div>

      {status?.configured ? (
        <>
          <div className="ai-provider-line">
            <span>{status.provider?.provider_id}</span>
            <strong>{status.provider?.model}</strong>
            <small>{status.provider?.endpoint_origin}</small>
          </div>
          <label className="ai-consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span>
              我同意将最多 256 个音符的结构化上下文发送到该模型。
              二进制 MIDI 和本地完整路径不会发送。
            </span>
          </label>
          <Button
            variant="secondary"
            disabled={!file || !consent || analyzing}
            onClick={analyze}
          >
            {analyzing
              ? <><LoaderCircle className="spin" size={15} /> 正在分析</>
              : <><BrainCircuit size={15} /> 生成 AI 建议</>}
          </Button>
        </>
      ) : !loadingStatus && (
        <p className="ai-unconfigured">
          设置 <code>FRETPILOT_LLM_BASE_URL</code>、<code>FRETPILOT_LLM_MODEL</code>
          和 <code>FRETPILOT_LLM_API_KEY</code> 后重启 API。
        </p>
      )}

      {report && (
        <div className="ai-shadow-result" aria-live="polite">
          <div><Check size={15} /><strong>建议已验证，但未应用</strong></div>
          <p>{report.summary || "模型没有提出高置信修改。"}</p>
          <span>
            接受 {report.accepted_decisions.length} 条 · 拒绝 {report.rejected_decisions.length} 条
            · 上下文 {report.context.note_count} notes
          </span>
        </div>
      )}
      {error && <p className="request-error" role="alert">{error}</p>}
      <div className="ai-shadow-note"><ShieldCheck size={13} /> 当前建议不会进入 GP5 或最终输出</div>
    </section>
  );
}
