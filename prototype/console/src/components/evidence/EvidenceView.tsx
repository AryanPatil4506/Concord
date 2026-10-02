import { CircleAlert, FlaskConical, Gauge, Layers3, ShieldCheck, Timer, TrendingDown, Zap } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { EmptyState, Segmented } from "../ui/ui";
import { CIBars, PolicyLegend, StressChart } from "./charts";
import { ABLATIONS, DOSSIER_EXTRA, LIMITS, POLICIES, SCALING, tri, type EvidenceData, type Policy, type Triple } from "./data";
import "./evidence.css";

type MetricId = "success" | "time_to_aid" | "report_latency" | "agents_lost_non_injected" | "energy";

const METRICS: Record<MetricId, { label: string; unit: string; fmt: (v: number) => string; lowerIsBetter: boolean; pairedKey?: string; max?: number }> = {
  success: { label: "Mission success", unit: "of missions", fmt: (v) => `${(v * 100).toFixed(1)}%`, lowerIsBetter: false, pairedKey: "success", max: 1 },
  time_to_aid: { label: "Time-to-aid", unit: "ticks, mean", fmt: (v) => v.toFixed(1), lowerIsBetter: true, pairedKey: "time_to_aid" },
  report_latency: { label: "Report latency", unit: "ticks, detection → base", fmt: (v) => v.toFixed(2), lowerIsBetter: true, pairedKey: "report_latency" },
  agents_lost_non_injected: { label: "Avoidable losses", unit: "assets per mission", fmt: (v) => v.toFixed(3), lowerIsBetter: true, pairedKey: "agents_lost_non_injected" },
  energy: { label: "Energy", unit: "units per mission", fmt: (v) => v.toFixed(0), lowerIsBetter: true, pairedKey: "energy" },
};

const STRESS_METRICS = {
  success: { label: "Success", fmt: (v: number) => `${Math.round(v * 100)}%`, yMax: 1, lower: false },
  agents_lost_non_injected: { label: "Avoidable losses", fmt: (v: number) => v.toFixed(2), yMax: 0.4, lower: true },
  time_to_aid: { label: "Time-to-aid", fmt: (v: number) => v.toFixed(0), yMax: 200, lower: true },
} as const;

function Section({ id, title, kicker, icon, children, aside }: { id: string; title: string; kicker?: string; icon: ReactNode; children: ReactNode; aside?: ReactNode }) {
  return (
    <section id={id} className="ev-section">
      <header className="ev-section-head">
        <div>
          <div className="ev-kicker">
            {icon}
            {kicker}
          </div>
          <h2>{title}</h2>
        </div>
        {aside}
      </header>
      {children}
    </section>
  );
}

function Tile({ value, label, sub, icon }: { value: string; label: string; sub: string; icon: ReactNode }) {
  return (
    <div className="ev-tile">
      <div className="ev-tile-icon">{icon}</div>
      <div className="ev-tile-value">{value}</div>
      <div className="ev-tile-label">{label}</div>
      <div className="ev-tile-sub num">{sub}</div>
    </div>
  );
}

export function EvidenceView() {
  const [data, setData] = useState<EvidenceData | null>(null);
  const [error, setError] = useState(false);
  const [metric, setMetric] = useState<MetricId>("time_to_aid");
  const [stressMetric, setStressMetric] = useState<keyof typeof STRESS_METRICS>("success");

  useEffect(() => {
    fetch("/api/evidence")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setData)
      .catch(() => setError(true));
  }, []);

  const values = useMemo(() => {
    if (!data) return null;
    const out = {} as Record<Policy, Triple>;
    POLICIES.forEach((p) => (out[p.id] = tri(data.main[p.id][metric])));
    return out;
  }, [data, metric]);

  const stressSeries = useMemo(() => {
    if (!data) return null;
    const levels = Object.keys(data.stress).sort((a, b) => Number(a) - Number(b));
    const out = {} as Record<Policy, number[]>;
    POLICIES.forEach((p) => (out[p.id] = levels.map((l) => tri(data.stress[l][p.id][stressMetric])[0])));
    return out;
  }, [data, stressMetric]);

  if (error)
    return (
      <div className="ev">
        <EmptyState icon={<CircleAlert size={16} />} title="Couldn't load results" body="Start the engine (python -m server) — the Evidence view reads results/summary.json." />
      </div>
    );
  if (!data || !values || !stressSeries)
    return (
      <div className="ev">
        <div className="skeleton" style={{ height: 120 }} />
        <div className="skeleton" style={{ height: 320 }} />
      </div>
    );

  const m = (p: Policy, k: string) => tri(data.main[p][k])[0];
  const six = data.stress["6"];
  const paired = METRICS[metric].pairedKey ? data.paired[METRICS[metric].pairedKey!] : undefined;
  const ttaGain = 1 - m("concord", "time_to_aid") / m("greedy", "time_to_aid");
  const latX = m("greedy", "report_latency") / m("concord", "report_latency");
  const lossGain = 1 - m("concord", "agents_lost_non_injected") / m("greedy", "agents_lost_non_injected");

  return (
    <div className="ev">
      <header className="ev-hero">
        <div className="eyebrow">Benchmark evidence · prototype v0</div>
        <h1>Faster aid, better-informed base, fewer lost drones.</h1>
        <p className="muted">
          {DOSSIER_EXTRA.scenarios} random flood scenarios ({DOSSIER_EXTRA.survivors.toLocaleString()} survivors, 3.2 disruptions on average) run under
          three policies with identical seeds and identical random draws — {DOSSIER_EXTRA.missions.toLocaleString()} missions including the stress
          sweep and ablations. 95% confidence intervals by bootstrap (4,000 resamples).
        </p>
        <nav className="ev-nav" aria-label="Sections">
          {[
            ["#headline", "Headline"],
            ["#compare", "Head-to-head"],
            ["#stress", "Stress"],
            ["#ablation", "Ablation"],
            ["#scaling", "Scaling"],
            ["#limits", "Limits"],
          ].map(([h, l]) => (
            <a key={h} href={h}>
              {l}
            </a>
          ))}
        </nav>
      </header>

      <div id="headline" className="ev-tiles">
        <Tile
          icon={<Timer />}
          value={`−${Math.round(ttaGain * 100)}%`}
          label="time-to-aid vs greedy"
          sub={`${m("concord", "time_to_aid").toFixed(1)} vs ${m("greedy", "time_to_aid").toFixed(1)} ticks`}
        />
        <Tile
          icon={<Zap />}
          value={`${Math.round(latX)}×`}
          label="faster critical reports"
          sub={`${m("concord", "report_latency").toFixed(2)} vs ${m("greedy", "report_latency").toFixed(2)} ticks`}
        />
        <Tile
          icon={<ShieldCheck />}
          value={`−${Math.round(lossGain * 100)}%`}
          label="avoidable asset losses"
          sub={`${m("concord", "agents_lost_non_injected").toFixed(3)} vs ${m("greedy", "agents_lost_non_injected").toFixed(3)} / mission`}
        />
        <Tile
          icon={<TrendingDown />}
          value={`${Math.round(tri(six.concord.success)[0] * 100)}% vs ${Math.round(tri(six.greedy.success)[0] * 100)}%`}
          label="success under 6 disruption types"
          sub={`static plan ${Math.round(tri(six.static.success)[0] * 100)}%`}
        />
      </div>

      <Section
        id="compare"
        kicker="Main benchmark"
        title="Head-to-head, 300 scenarios"
        icon={<Gauge />}
        aside={
          <Segmented
            label="Metric"
            size="sm"
            value={metric}
            onChange={setMetric}
            options={(Object.keys(METRICS) as MetricId[]).map((k) => ({ value: k, label: METRICS[k].label }))}
          />
        }
      >
        <div className="ev-card">
          <div className="ev-card-head">
            <div>
              <h3>{METRICS[metric].label}</h3>
              <p className="subtle">
                {METRICS[metric].unit} · {METRICS[metric].lowerIsBetter ? "lower is better" : "higher is better"} · whiskers = 95% CI
              </p>
            </div>
            <PolicyLegend />
          </div>
          <CIBars values={values} format={METRICS[metric].fmt} max={METRICS[metric].max} lowerIsBetter={METRICS[metric].lowerIsBetter} />
          {paired && (
            <p className="ev-paired num">
              Paired difference, CONCORD − greedy: <strong>{metric === "success" ? `${(paired[0] * 100).toFixed(1)} pts` : paired[0].toFixed(metric === "agents_lost_non_injected" ? 3 : 2)}</strong>{" "}
              [{metric === "success" ? (paired[1] * 100).toFixed(1) : paired[1].toFixed(metric === "agents_lost_non_injected" ? 3 : 2)},{" "}
              {metric === "success" ? (paired[2] * 100).toFixed(1) : paired[2].toFixed(metric === "agents_lost_non_injected" ? 3 : 2)}]
            </p>
          )}
        </div>

        <details className="ev-card ev-details">
          <summary>
            <span>All metrics</span>
            <span className="subtle">table · mean [95% CI]</span>
          </summary>
          <div className="ev-table-wrap">
            <table className="ev-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {POLICIES.map((p) => (
                    <th key={p.id} className="r">
                      <span className="ev-th-policy">
                        <i style={{ background: p.color }} />
                        {p.name}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["Mission success", (p: Policy) => ci(data.main[p].success, (v) => `${(v * 100).toFixed(1)}%`)],
                  ["Survivors aided", (p: Policy) => `${(m(p, "delivered_frac") * 100).toFixed(1)}%`],
                  ["Mean time-to-aid (ticks)", (p: Policy) => ci(data.main[p].time_to_aid, (v) => v.toFixed(1))],
                  ["Median time-to-aid (ticks)", (p: Policy) => String(DOSSIER_EXTRA.median_tta[p])],
                  ["Aided within 120 ticks", (p: Policy) => `${(DOSSIER_EXTRA.within_120[p] * 100).toFixed(1)}%`],
                  ["Critical-report latency (ticks)", (p: Policy) => ci(data.main[p].report_latency, (v) => v.toFixed(2))],
                  ["Avoidable asset losses / mission", (p: Policy) => ci(data.main[p].agents_lost_non_injected, (v) => v.toFixed(3))],
                  ["All asset losses / mission", (p: Policy) => m(p, "agents_lost").toFixed(2)],
                  ["Energy used", (p: Policy) => m(p, "energy").toFixed(0)],
                  ["Reassignments / mission", (p: Policy) => (p === "concord" ? m(p, "churn").toFixed(2) : "–")],
                  ["Wall time / mission", (p: Policy) => `${DOSSIER_EXTRA.wall_ms[p]} ms`],
                ].map(([label, f]) => (
                  <tr key={label as string}>
                    <td>{label as string}</td>
                    {POLICIES.map((p) => (
                      <td key={p.id} className={`r num ${p.id === "concord" ? "is-concord" : ""}`}>
                        {(f as (p: Policy) => string)(p.id)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="subtle ev-foot">Median, within-120 and wall time from the research dossier §4.1; everything else from results/summary.json.</p>
        </details>
      </Section>

      <Section
        id="stress"
        kicker="Stress sweep"
        title="The gap widens as the world gets worse"
        icon={<TrendingDown />}
        aside={
          <Segmented
            label="Stress metric"
            size="sm"
            value={stressMetric}
            onChange={setStressMetric}
            options={(Object.keys(STRESS_METRICS) as (keyof typeof STRESS_METRICS)[]).map((k) => ({ value: k, label: STRESS_METRICS[k].label }))}
          />
        }
      >
        <div className="ev-card">
          <StressChart
            series={stressSeries}
            format={STRESS_METRICS[stressMetric].fmt}
            yMax={STRESS_METRICS[stressMetric].yMax}
            lowerIsBetter={STRESS_METRICS[stressMetric].lower}
          />
          <PolicyLegend />
        </div>
      </Section>

      <Section id="ablation" kicker="Ablation" title="What each component buys" icon={<FlaskConical />}>
        <div className="ev-card ev-table-wrap">
          <table className="ev-table">
            <thead>
              <tr>
                <th>Variant (same 300 seeds)</th>
                <th className="r">Success</th>
                <th className="r">Time-to-aid</th>
                <th className="r">Report latency</th>
                <th className="r">Avoidable losses</th>
                <th className="r">Churn</th>
                <th className="r">Energy</th>
              </tr>
            </thead>
            <tbody>
              {ABLATIONS.map((a) => {
                const row = data.ablation[a.id];
                const full = data.ablation.full;
                const cell = (k: string, f: (v: number) => string, worseIfHigher: boolean, factor = 1.25) => {
                  const v = tri(row[k])[0];
                  const ref = tri(full[k])[0];
                  const bad = a.id !== "full" && (worseIfHigher ? v > ref * factor : v < ref / factor);
                  return <td className={`r num ${bad ? "is-worse" : ""}`}>{f(v)}</td>;
                };
                return (
                  <tr key={a.id} className={a.id === "full" ? "is-ref" : ""}>
                    <td>
                      <div className="ev-abl-name">{a.label}</div>
                      {a.id !== "full" && <div className="subtle ev-abl-read">{a.readout}</div>}
                    </td>
                    {cell("success", (v) => `${(v * 100).toFixed(1)}%`, false, 1.02)}
                    {cell("time_to_aid", (v) => v.toFixed(1), true, 1.02)}
                    {cell("report_latency", (v) => v.toFixed(2), true)}
                    {cell("agents_lost_non_injected", (v) => v.toFixed(3), true)}
                    {cell("churn", (v) => v.toFixed(2), true, 3)}
                    {cell("energy", (v) => v.toFixed(0), true, 1.05)}
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="subtle ev-foot">Highlighted cells: a clearly worse value than full CONCORD. Reported even when unflattering (battery invariant, hysteresis energy cost).</p>
        </div>
      </Section>

      <Section id="scaling" kicker="Scaling" title="Repair re-plans stay under 10 ms at 200 agents" icon={<Layers3 />}>
        <div className="ev-card ev-table-wrap">
          <table className="ev-table ev-scaling">
            <thead>
              <tr>
                <th>Agents / tasks</th>
                <th>Repair re-plan</th>
                <th>Global re-plan</th>
                <th className="r">Cold distance maps</th>
              </tr>
            </thead>
            <tbody>
              {SCALING.map((s) => (
                <tr key={s.agents}>
                  <td className="num">
                    {s.agents} / {s.tasks}
                  </td>
                  <td>
                    <LogBar ms={s.repair} tone="concord" />
                  </td>
                  <td>
                    <LogBar ms={s.global} tone="muted" />
                  </td>
                  <td className="r num">{fmtMs(s.cold)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="subtle ev-foot">
            1 CPU core, pure Python, 3 tasks per agent, warm distance maps (log scale). Global re-plans grow roughly with T² and run asynchronously while agents keep
            executing; repair — the common case — stays under 10 ms. Reproduce with <span className="mono">scaling.py</span>.
          </p>
        </div>
      </Section>

      <Section id="limits" kicker="Honest limits" title="What v0 does not prove yet" icon={<CircleAlert />}>
        <ol className="ev-limits">
          {LIMITS.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ol>
      </Section>
    </div>
  );
}

function ci(v: Triple | number, f: (x: number) => string) {
  const [m, lo, hi] = tri(v);
  return `${f(m)} [${f(lo)}, ${f(hi)}]`;
}

function fmtMs(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${ms < 10 ? ms.toFixed(2) : ms.toFixed(ms < 100 ? 1 : 0)} ms`;
}

function LogBar({ ms, tone }: { ms: number; tone: "concord" | "muted" }) {
  const lo = Math.log10(0.1);
  const hi = Math.log10(3000);
  const w = ((Math.log10(ms) - lo) / (hi - lo)) * 100;
  return (
    <span className="logbar">
      <span className={`logbar-fill lb-${tone}`} style={{ width: `${Math.max(2, w)}%` }} />
      <span className="num">{fmtMs(ms)}</span>
    </span>
  );
}
