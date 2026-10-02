import { Activity, AlertTriangle, CheckCircle2, TrendingDown } from "lucide-react";
import { useMemo, useState } from "react";
import { useSize } from "../../lib/hooks";
import { forecastStatus, pct } from "../../lib/meta";
import type { ForecastPoint } from "../../lib/types";
import { Badge, SectionHeader, Spinner } from "../ui/ui";
import "./forecast.css";

interface Props {
  timeline: ForecastPoint[];
  t: number;
  tmax: number;
  threshold: number;
  assessing: string | null;
  k?: number;
}

export function ForecastPanel({ timeline, t, tmax, threshold, assessing, k = 40 }: Props) {
  const points = useMemo(() => [...timeline].sort((a, b) => a.t - b.t || (a.kind === "assess" ? 1 : -1)), [timeline]);
  const latest = points.length ? points.reduce((a, b) => (b.t >= a.t ? b : a)) : null;
  const status = latest ? forecastStatus(latest.p, threshold) : null;
  const StatusIcon = status?.tone === "good" ? CheckCircle2 : status?.tone === "warning" ? TrendingDown : AlertTriangle;

  return (
    <section className="panel forecast" aria-label="Feasibility forecast">
      <SectionHeader
        title="Feasibility forecast"
        icon={<Activity />}
        info={`P(mission success) from ${k} Monte-Carlo rollouts of the current plan, with future disruptions sampled from the prior. Re-run every 10 ticks and right after every disruption. Below ${pct(threshold)} the operator gets a decision card. In v0 the hazard model matches the simulator, so calibration is optimistic.`}
        actions={
          assessing ? (
            <Badge tone="accent" icon={<Spinner size={10} />}>
              Re-forecasting
            </Badge>
          ) : status ? (
            <Badge tone={status.tone} icon={<StatusIcon />}>
              {status.label}
            </Badge>
          ) : null
        }
      />
      <div className="forecast-hero">
        <div className={`forecast-value num tone-text-${status?.tone ?? "muted"}`}>
          {latest ? Math.round(latest.p * 100) : "—"}
          <span>%</span>
        </div>
        <div className="forecast-meta">
          <div className="forecast-caption">P(mission success)</div>
          <div className="subtle num">
            {latest ? `${k} rollouts · updated t=${latest.t}` : "First forecast running…"}
          </div>
          <div className="subtle">Escalates below {pct(threshold)}</div>
        </div>
      </div>
      <ForecastChart points={points} t={t} tmax={tmax} threshold={threshold} />
    </section>
  );
}

function ForecastChart({ points, t, tmax, threshold }: { points: ForecastPoint[]; t: number; tmax: number; threshold: number }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hover, setHover] = useState<ForecastPoint | null>(null);
  const h = 104;
  const pad = { l: 28, r: 8, t: 8, b: 18 };
  const iw = Math.max(10, width - pad.l - pad.r);
  const ih = h - pad.t - pad.b;
  const x = (v: number) => pad.l + (v / tmax) * iw;
  const y = (p: number) => pad.t + (1 - p) * ih;
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.p).toFixed(1)}`).join("");
  const area = points.length ? `${line}L${x(points[points.length - 1].t)},${y(0)}L${x(points[0].t)},${y(0)}Z` : "";

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!points.length) return;
    const r = e.currentTarget.getBoundingClientRect();
    const tv = ((e.clientX - r.left - pad.l) / iw) * tmax;
    let best = points[0];
    for (const p of points) if (Math.abs(p.t - tv) < Math.abs(best.t - tv)) best = p;
    setHover(best);
  };

  return (
    <div className="forecast-chart" ref={ref}>
      {width > 0 && (
        <svg width={width} height={h} onMouseMove={onMove} onMouseLeave={() => setHover(null)} role="img" aria-label="Forecast over mission time">
          <defs>
            <linearGradient id="fc-area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.22" />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 0.5, 1].map((g) => (
            <g key={g}>
              <line x1={pad.l} x2={pad.l + iw} y1={y(g)} y2={y(g)} className="fc-grid" />
              <text x={pad.l - 6} y={y(g)} className="fc-axis" textAnchor="end" dominantBaseline="middle">
                {g * 100}%
              </text>
            </g>
          ))}
          <rect x={pad.l} y={y(threshold)} width={iw} height={y(0) - y(threshold)} className="fc-danger" />
          <line x1={pad.l} x2={pad.l + iw} y1={y(threshold)} y2={y(threshold)} className="fc-threshold" />
          <text x={pad.l + iw} y={y(threshold) - 4} className="fc-axis fc-threshold-label" textAnchor="end">
            escalate &lt; {Math.round(threshold * 100)}%
          </text>
          {[0, Math.round(tmax / 2), tmax].map((v) => (
            <text key={v} x={x(v)} y={h - 4} className="fc-axis" textAnchor={v === 0 ? "start" : v === tmax ? "end" : "middle"}>
              t={v}
            </text>
          ))}
          <line x1={x(t)} x2={x(t)} y1={pad.t} y2={y(0)} className="fc-now" />
          {area && <path d={area} fill="url(#fc-area)" />}
          {line && <path d={line} className="fc-line" />}
          {points
            .filter((p) => p.kind === "assess")
            .map((p) => (
              <circle
                key={`a${p.t}`}
                cx={x(p.t)}
                cy={y(p.p)}
                r={4}
                className={p.p < threshold ? "fc-dot fc-dot-crit" : "fc-dot"}
              />
            ))}
          {hover && (
            <g>
              <line x1={x(hover.t)} x2={x(hover.t)} y1={pad.t} y2={y(0)} className="fc-cross" />
              <circle cx={x(hover.t)} cy={y(hover.p)} r={4.5} className="fc-hover-dot" />
            </g>
          )}
        </svg>
      )}
      {hover && (
        <div
          className="fc-tip"
          style={{ left: Math.min(Math.max(x(hover.t), 70), width - 70) }}
        >
          <strong className="num">{pct(hover.p)}</strong>
          <span className="subtle num">
            t={hover.t} · {hover.kind === "assess" ? "after disruption" : "periodic"}
          </span>
        </div>
      )}
      <div className="fc-legend">
        <span><i className="fc-key-line" /> Forecast</span>
        <span><i className="fc-key-dot" /> After a disruption</span>
        <span><i className="fc-key-now" /> Now</span>
      </div>
    </div>
  );
}
