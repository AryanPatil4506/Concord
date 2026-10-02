import { useState } from "react";
import { useSize } from "../../lib/hooks";
import { POLICIES, type Policy, type Triple } from "./data";

export function PolicyLegend({ only }: { only?: Policy[] }) {
  return (
    <div className="ev-legend">
      {POLICIES.filter((p) => !only || only.includes(p.id)).map((p) => (
        <span key={p.id}>
          <i style={{ background: p.color }} />
          {p.name}
        </span>
      ))}
    </div>
  );
}

export function CIBars({
  values,
  format,
  max,
  lowerIsBetter,
}: {
  values: Record<Policy, Triple>;
  format: (v: number) => string;
  max?: number;
  lowerIsBetter?: boolean;
}) {
  const [hover, setHover] = useState<Policy | null>(null);
  const top = max ?? Math.max(...POLICIES.map((p) => values[p.id][2])) * 1.08;
  const best = POLICIES.reduce((a, b) =>
    (lowerIsBetter ? values[b.id][0] < values[a.id][0] : values[b.id][0] > values[a.id][0]) ? b : a,
  ).id;
  return (
    <div className="cibars" role="table">
      {POLICIES.map((p) => {
        const [m, lo, hi] = values[p.id];
        return (
          <div
            key={p.id}
            className={`cibar-row ${hover && hover !== p.id ? "is-dim" : ""}`}
            role="row"
            onMouseEnter={() => setHover(p.id)}
            onMouseLeave={() => setHover(null)}
          >
            <span className="cibar-name" role="rowheader">
              {p.name}
            </span>
            <span className="cibar-track" role="cell">
              <span className="cibar-fill" style={{ width: `${(m / top) * 100}%`, background: p.color }} />
              {hi > lo && (
                <span className="cibar-ci" style={{ left: `${(lo / top) * 100}%`, width: `${((hi - lo) / top) * 100}%` }} />
              )}
              {hover === p.id && (
                <span className="cibar-tip num">
                  {format(m)} · 95% CI [{format(lo)}, {format(hi)}]
                </span>
              )}
            </span>
            <span className={`cibar-val num ${best === p.id ? "is-best" : ""}`} role="cell">
              {format(m)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function StressChart({
  series,
  format,
  yMax,
  lowerIsBetter,
}: {
  series: Record<Policy, number[]>;
  format: (v: number) => string;
  yMax: number;
  lowerIsBetter?: boolean;
}) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hx, setHx] = useState<number | null>(null);
  const h = 240;
  const pad = { l: 44, r: 108, t: 12, b: 30 };
  const iw = Math.max(40, width - pad.l - pad.r);
  const ih = h - pad.t - pad.b;
  const n = series.concord.length;
  const x = (i: number) => pad.l + (i / (n - 1)) * iw;
  const y = (v: number) => pad.t + (1 - v / yMax) * ih;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);
  return (
    <div className="stress" ref={ref}>
      {width > 0 && (
        <svg
          width={width}
          height={h}
          role="img"
          aria-label="Stress sweep chart"
          onMouseMove={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            const i = Math.round(((e.clientX - r.left - pad.l) / iw) * (n - 1));
            setHx(i >= 0 && i < n ? i : null);
          }}
          onMouseLeave={() => setHx(null)}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line x1={pad.l} x2={pad.l + iw} y1={y(t)} y2={y(t)} className="ch-grid" />
              <text x={pad.l - 8} y={y(t)} className="ch-axis" textAnchor="end" dominantBaseline="middle">
                {format(t)}
              </text>
            </g>
          ))}
          {series.concord.map((_, i) => (
            <text key={i} x={x(i)} y={h - 10} className="ch-axis" textAnchor="middle">
              {i}
            </text>
          ))}
          {hx != null && <line x1={x(hx)} x2={x(hx)} y1={pad.t} y2={pad.t + ih} className="ch-cross" />}
          {POLICIES.map((p) => {
            const vals = series[p.id];
            const d = vals.map((v, i) => `${i ? "L" : "M"}${x(i)},${y(v)}`).join("");
            const last = vals[vals.length - 1];
            return (
              <g key={p.id}>
                <path d={d} fill="none" stroke={p.color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
                {vals.map((v, i) => (
                  <circle key={i} cx={x(i)} cy={y(v)} r={hx === i ? 4.5 : 3} fill={p.color} stroke="var(--surface-1)" strokeWidth={2} />
                ))}
                <text x={x(n - 1) + 10} y={y(last)} className="ch-direct" dominantBaseline="middle">
                  {p.name} {format(last)}
                </text>
              </g>
            );
          })}
        </svg>
      )}
      {hx != null && width > 0 && (
        <div className="stress-tip" style={{ left: Math.min(x(hx) + 12, width - 190) }}>
          <div className="stress-tip-title">
            {hx} disruption type{hx === 1 ? "" : "s"}
          </div>
          {[...POLICIES]
            .sort((a, b) => (lowerIsBetter ? series[a.id][hx] - series[b.id][hx] : series[b.id][hx] - series[a.id][hx]))
            .map((p) => (
              <div key={p.id} className="stress-tip-row">
                <i style={{ background: p.color }} />
                <span>{p.name}</span>
                <strong className="num">{format(series[p.id][hx])}</strong>
              </div>
            ))}
        </div>
      )}
      <div className="ch-xlabel subtle">Disruption types forced per mission (100 scenarios per level)</div>
    </div>
  );
}
