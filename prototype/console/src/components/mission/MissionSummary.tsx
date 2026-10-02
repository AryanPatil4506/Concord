import { CircleCheckBig, CircleAlert, Download, Eye, RotateCcw, UserCheck, Zap } from "lucide-react";
import { fmt, pct } from "../../lib/meta";
import type { MissionMetrics, MissionSnapshot } from "../../lib/types";
import { Badge, Button, Modal } from "../ui/ui";
import "./summary.css";

const POLICY_COLOR: Record<string, string> = {
  you: "var(--policy-concord)",
  concord: "rgba(57, 135, 229, 0.55)",
  greedy: "var(--policy-greedy)",
  static: "var(--policy-static)",
};

function download(name: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function MissionSummary({
  mission,
  open,
  onClose,
  onNew,
}: {
  mission: MissionSnapshot;
  open: boolean;
  onClose: () => void;
  onNew: () => void;
}) {
  const s = mission.summary;
  if (!s) return null;
  const m = s.metrics;
  const aided = Math.round(m.delivered_frac * m.survivors);
  const ok = m.success === 1;
  const rows: { key: string; name: string; m: MissionMetrics; note?: string }[] = [
    { key: "you", name: "CONCORD (this run)", m, note: s.escalations.length ? "with your decisions" : undefined },
    ...s.baselines.map((b) => ({ key: b.policy, name: b.name, m: b.metrics })),
  ];

  return (
    <Modal open={open} onClose={onClose} width={760} label="Mission summary">
      <div className="sum">
        <header className="sum-head">
          <div className={`sum-icon ${ok ? "is-ok" : "is-bad"}`}>{ok ? <CircleCheckBig /> : <CircleAlert />}</div>
          <div>
            <div className="eyebrow">Mission {ok ? "complete" : "ended"} · t={m.makespan}</div>
            <h2>
              {ok ? `All ${m.survivors} survivors aided` : `${aided} of ${m.survivors} survivors aided`}
            </h2>
            <p className="muted">
              {s.last_aid_t != null && `Last aid at t=${s.last_aid_t} · `}
              {s.disruptions.length} disruption{s.disruptions.length === 1 ? "" : "s"} · {s.escalations.length} human decision
              {s.escalations.length === 1 ? "" : "s"} · {m.agents_lost_non_injected} avoidable loss
              {m.agents_lost_non_injected === 1 ? "" : "es"}
            </p>
          </div>
        </header>

        <div className="sum-metrics">
          {[
            ["Mean time-to-aid", `${fmt(m.time_to_aid, 1)} ticks`],
            ["Report latency", Number.isNaN(m.report_latency) || m.report_latency == null ? "—" : `${fmt(m.report_latency, 2)} ticks`],
            ["Agents lost", `${m.agents_lost} (${m.agents_lost_non_injected} avoidable)`],
            ["Survey coverage", pct(m.coverage)],
            ["Energy used", fmt(m.energy, 0)],
            ["Reassignments", String(m.churn)],
          ].map(([k, v]) => (
            <div key={k} className="sum-metric">
              <div className="subtle">{k}</div>
              <div className="num">{v}</div>
            </div>
          ))}
        </div>

        <section className="sum-section">
          <div className="sum-section-head">
            <h3>Same map, same disruptions</h3>
            <span className="subtle">Paired re-runs on seed {mission.static.seed}</span>
          </div>
          <div className="cmp">
            <div className="cmp-row cmp-header subtle">
              <span>Policy</span>
              <span>Survivors aided</span>
              <span className="r">Time-to-aid</span>
              <span className="r">Lost</span>
            </div>
            {rows.map((r) => {
              const n = Math.round(r.m.delivered_frac * r.m.survivors);
              return (
                <div key={r.key} className={`cmp-row ${r.key === "you" ? "is-you" : ""}`}>
                  <span className="cmp-name">
                    <i style={{ background: POLICY_COLOR[r.key] }} />
                    <span>
                      {r.name}
                      {r.note && <span className="subtle"> · {r.note}</span>}
                    </span>
                  </span>
                  <span className="cmp-bar">
                    <span className="cmp-track">
                      <span className="cmp-fill" style={{ width: `${r.m.delivered_frac * 100}%`, background: POLICY_COLOR[r.key] }} />
                    </span>
                    <span className="num">
                      {n}/{r.m.survivors}
                    </span>
                  </span>
                  <span className="r num">{fmt(r.m.time_to_aid, 0)}</span>
                  <span className="r num">{r.m.agents_lost}</span>
                </div>
              );
            })}
          </div>
          <p className="subtle sum-note">
            Baselines cannot escalate, so they run without operator decisions. Time-to-aid counts never-aided survivors at the horizon.
          </p>
        </section>

        <div className="sum-two">
          <section className="sum-section">
            <div className="sum-section-head">
              <h3>Disruptions</h3>
            </div>
            <ul className="sum-list">
              {s.disruptions.length === 0 && <li className="subtle">None</li>}
              {s.disruptions.map((d, i) => (
                <li key={i}>
                  <Zap size={13} />
                  <span>{d.label}</span>
                  <span className="subtle num">t={d.t}</span>
                  {s.injected.some((x) => x.t === d.t && x.kind === d.kind) && <Badge>injected</Badge>}
                </li>
              ))}
            </ul>
          </section>
          <section className="sum-section">
            <div className="sum-section-head">
              <h3>Human decisions</h3>
            </div>
            <ul className="sum-list">
              {s.escalations.length === 0 && <li className="subtle">No escalations — the swarm handled every disruption.</li>}
              {s.escalations.map((e, i) => (
                <li key={i}>
                  <UserCheck size={13} />
                  <span>
                    Option {e.chosen}: {e.title}
                  </span>
                  <span className="subtle num">
                    t={e.t} · {pct(e.p_now)} → {pct(e.p)}
                  </span>
                  {e.auto && <Badge tone="warning">safe default</Badge>}
                </li>
              ))}
            </ul>
          </section>
        </div>

        <footer className="sum-foot">
          <Button
            variant="ghost"
            icon={<Download size={15} />}
            onClick={() =>
              download(`concord-run-seed${mission.static.seed}.json`, {
                scenario: mission.scenario,
                objective: mission.objective,
                ...s,
                log: mission.log,
                forecasts: mission.timeline,
              })
            }
          >
            Download run log
          </Button>
          <div className="sum-foot-right">
            <Button variant="secondary" icon={<Eye size={15} />} onClick={onClose}>
              Review map
            </Button>
            <Button variant="primary" icon={<RotateCcw size={15} />} onClick={onNew}>
              New mission
            </Button>
          </div>
        </footer>
      </div>
    </Modal>
  );
}
