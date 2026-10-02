import { Bot, Clock4, HeartHandshake, Map as MapIcon, RadioReceiver, Zap } from "lucide-react";
import type { ReactNode } from "react";
import { fmt } from "../../lib/meta";
import type { LiveMetrics } from "../../lib/types";
import { Tooltip } from "../ui/ui";
import "./kpi.css";

function Kpi({
  icon,
  label,
  value,
  unit,
  sub,
  tone,
  info,
}: {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
  tone?: "good" | "warning" | "critical";
  info: string;
}) {
  return (
    <Tooltip content={info} side="bottom" className="tt-wide kpi-tt">
      <div className={`kpi ${tone ? `kpi-${tone}` : ""}`} tabIndex={0}>
        <div className="kpi-label">
          {icon}
          {label}
        </div>
        <div className="kpi-value num">
          {value}
          {unit && <span className="kpi-unit">{unit}</span>}
        </div>
        {sub && <div className="kpi-sub">{sub}</div>}
      </div>
    </Tooltip>
  );
}

export function KpiStrip({ m }: { m: LiveMetrics }) {
  return (
    <div className="kpi-strip" aria-label="Mission metrics">
      <Kpi
        icon={<HeartHandshake />}
        label="Survivors aided"
        value={
          <>
            {m.aided}
            <span className="kpi-of">/ {m.found}</span>
          </>
        }
        sub={
          m.awaiting > 0 ? (
            <span className="tone-text-critical">{m.awaiting} awaiting aid</span>
          ) : m.unreported > 0 ? (
            <span className="tone-text-warning">{m.unreported} report pending</span>
          ) : (
            "found so far"
          )
        }
        info="Med-kits delivered out of survivors found so far. Success = every survivor aided before the horizon."
      />
      <Kpi
        icon={<Clock4 />}
        label="Mean time-to-aid"
        value={fmt(m.mean_tta, 0)}
        unit={m.mean_tta != null ? "ticks" : undefined}
        sub={m.mean_tta != null ? `≈ ${Math.round((m.mean_tta * 10) / 60)} min` : "no deliveries yet"}
        info="Delivery tick minus appearance tick, averaged over aided survivors. Benchmark: CONCORD 62.4, greedy 71.1."
      />
      <Kpi
        icon={<RadioReceiver />}
        label="Report latency"
        value={fmt(m.report_latency, 1)}
        unit={m.report_latency != null ? "ticks" : undefined}
        sub="detection → base"
        info="Ticks from a scout seeing a survivor to base knowing. Value-of-information messaging keeps this near zero (benchmark 0.84 vs 8.71 greedy)."
      />
      <Kpi
        icon={<Bot />}
        label="Fleet"
        value={
          <>
            {m.agents_up}
            <span className="kpi-of">/ {m.agents_total}</span>
          </>
        }
        tone={m.lost_avoidable > 0 ? "critical" : undefined}
        sub={
          m.agents_total - m.agents_up > 0
            ? `${m.lost_injected} failed · ${m.lost_avoidable} avoidable`
            : `${m.connected} linked to base`
        }
        info="Operational agents. Avoidable losses (storm, battery depletion) are tracked separately from injected hardware failures."
      />
      <Kpi
        icon={<MapIcon />}
        label="Survey coverage"
        value={
          <>
            {m.surveyed}
            <span className="kpi-of">/ {m.surveys_total}</span>
          </>
        }
        sub="waypoints surveyed"
        info="Survey waypoints visited by scout cameras across sectors A–D."
      />
      <Kpi
        icon={<Zap />}
        label="Disruptions"
        value={m.disruptions}
        sub={`${m.decisions} needed a human`}
        info={`Disruptions so far and how many needed a human decision. Plan churn so far: ${m.reassignments} task reassignment${m.reassignments === 1 ? "" : "s"} between agents.`}
      />
    </div>
  );
}
