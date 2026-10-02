import { BatteryLow, Circle, CircleCheck, MapPin, XOctagon } from "lucide-react";
import type { ReactNode } from "react";
import { AGENT_META, batteryTone, cleanLogText, LOG_META, pct, splitDetail } from "../../lib/meta";
import type { DisruptionKind, LogEntry, MissionSnapshot } from "../../lib/types";
import { AgentGlyph, SURVIVOR_META, SurvivorGlyph, survivorStatus } from "../glyphs";
import type { Selection } from "../map/MissionMap";
import { Badge, Button, Drawer, Meter } from "../ui/ui";
import "./drawer.css";

interface Props {
  mission: MissionSnapshot;
  selection: Selection;
  onClose: () => void;
  onInject: (kind: DisruptionKind, params?: Record<string, unknown>) => void;
  injectBlocked: string | null;
}

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="dstat">
      <div className="dstat-label">{label}</div>
      <div className="dstat-value num">{children}</div>
    </div>
  );
}

function RelatedLog({ entries }: { entries: LogEntry[] }) {
  if (!entries.length) return <p className="subtle d-empty">No decisions involving this yet.</p>;
  return (
    <ol className="d-log">
      {entries.map((e) => {
        const meta = LOG_META[e.kind] ?? LOG_META.assign;
        const Icon = meta.icon;
        const [main, detail] = splitDetail(cleanLogText(e.text));
        return (
          <li key={e.i} className={`tone-${meta.tone}`}>
            <span className="num subtle">t={e.t}</span>
            <Icon />
            <span>
              {main}
              {detail && <span className="subtle"> · {detail}</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export function DetailDrawer({ mission, selection, onClose, onInject, injectBlocked }: Props) {
  const { state, static: st, log } = mission;

  if (selection?.type === "agent") {
    const a = state.agents.find((x) => x.id === selection.id);
    const spec = st.fleet.find((f) => f.id === selection.id);
    if (!a || !spec) return null;
    const related = log.filter((e) => e.agent === a.id || e.text.includes(a.id)).slice(-8).reverse();
    return (
      <Drawer
        open
        onClose={onClose}
        icon={<AgentGlyph kind={a.kind} size={20} lost={!a.alive} />}
        title={a.id}
        subtitle={`${AGENT_META[a.kind].label} · ${AGENT_META[a.kind].role}`}
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              icon={<BatteryLow size={14} />}
              disabled={!a.alive || !!injectBlocked}
              title={injectBlocked ?? undefined}
              onClick={() => onInject("battery_drain", { agent: a.id })}
            >
              Drain battery −45%
            </Button>
            <Button
              variant="danger"
              size="sm"
              icon={<XOctagon size={14} />}
              disabled={!a.alive || !!injectBlocked}
              title={injectBlocked ?? undefined}
              onClick={() => onInject("agent_fail", { agent: a.id })}
            >
              Simulate hardware failure
            </Button>
          </>
        }
      >
        <div className="d-badges">
          {!a.alive ? (
            <Badge tone="critical">Lost · {a.lost_why}</Badge>
          ) : (
            <>
              <Badge tone={a.conn ? "good" : "critical"} dot>
                {a.conn ? "Linked to base" : "No link"}
              </Badge>
              {a.status === "charging" && <Badge tone="accent">Charging</Badge>}
              {a.storm_exposed && <Badge tone="warning">Inside storm</Badge>}
              {a.queued_critical > 0 && <Badge tone="warning">{a.queued_critical} critical report queued</Badge>}
            </>
          )}
        </div>

        <section className="d-section">
          <div className="eyebrow">Now</div>
          <p className="d-activity">{a.activity}</p>
          {a.alive && (
            <div className="d-batt">
              <Meter value={a.batt} tone={batteryTone(a.batt)} height={6} label="Battery" />
              <span className="num">{pct(a.batt)}</span>
            </div>
          )}
        </section>

        <section className="d-grid">
          {spec.kits > 0 && (
            <Stat label="Med-kits">
              {a.kits}/{a.kit_cap}
            </Stat>
          )}
          <Stat label="Speed">{spec.speed} cells/tick</Stat>
          <Stat label="Battery capacity">{spec.battery}</Stat>
          <Stat label="Radio range">{spec.comm} cells</Stat>
          <Stat label="Energy used">{a.energy.toFixed(0)}</Stat>
          <Stat label="Messages queued">{a.queued}</Stat>
          <Stat label="Position">
            ({a.pos[0]}, {a.pos[1]})
          </Stat>
          <Stat label="Mobility">{spec.aerial ? "Aerial · weather-sensitive" : "Ground · bridges only"}</Stat>
        </section>

        <section className="d-section">
          <div className="eyebrow">Capabilities</div>
          <div className="d-badges">
            {spec.caps.map((c) => (
              <Badge key={c}>{c}</Badge>
            ))}
            {spec.sensor > 0 && <Badge>detects within {spec.sensor} cells</Badge>}
          </div>
        </section>

        <section className="d-section">
          <div className="eyebrow">Plan · task bundle</div>
          {a.plan.length ? (
            <ol className="d-plan">
              {a.plan.map((p, i) => (
                <li key={i} className={i === 0 ? "is-current" : ""}>
                  <span className="d-plan-dot">{i === 0 ? <MapPin size={12} /> : <Circle size={8} />}</span>
                  <span>{p.label}</span>
                  <span className="subtle num">
                    ({p.pos[0]}, {p.pos[1]})
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="subtle d-empty">{a.alive ? "No tasks — standing by." : "Tasks were released and re-auctioned."}</p>
          )}
        </section>

        <section className="d-section">
          <div className="eyebrow">Recent decisions</div>
          <RelatedLog entries={related} />
        </section>
      </Drawer>
    );
  }

  if (selection?.type === "survivor") {
    const s = state.survivors.find((x) => x.sid === selection.id);
    if (!s) return null;
    const status = survivorStatus(s);
    const related = log
      .filter((e) => e.sid === s.sid || new RegExp(`\\b${s.sid}\\b`).test(e.text))
      .slice(-8)
      .reverse();
    const detectedBy = log.find((e) => e.kind === "detect" && e.sid === s.sid)?.agent;
    const deliveredBy = log.find((e) => e.kind === "deliver" && e.sid === s.sid)?.agent;
    const steps = [
      {
        label: s.by_call ? "Emergency call received" : "Trapped (ground truth)",
        t: s.appear_t,
        done: true,
        note: s.by_call ? "Reported directly to base" : "Unknown to the swarm",
      },
      {
        label: "Detected",
        t: s.detected_t,
        done: s.detected_t != null,
        note: s.by_call ? "Via call" : detectedBy ? `By ${detectedBy}` : undefined,
      },
      {
        label: "Reported to base",
        t: s.reported_t,
        done: s.reported_t != null,
        note:
          s.reported_t != null && s.detected_t != null && !s.by_call
            ? `${s.reported_t - s.detected_t} ticks after detection`
            : undefined,
      },
      {
        label: "Med-kit delivered",
        t: s.delivered_t,
        done: s.delivered_t != null,
        note:
          s.delivered_t != null
            ? `${deliveredBy ? `By ${deliveredBy} · ` : ""}time-to-aid ${s.delivered_t - s.appear_t} ticks`
            : s.assignee
              ? `Assigned to ${s.assignee}`
              : s.reported_t != null
                ? "Waiting for a capable agent"
                : undefined,
      },
    ];
    return (
      <Drawer
        open
        onClose={onClose}
        icon={<SurvivorGlyph status={status} size={20} />}
        title={`Survivor ${s.sid}`}
        subtitle={`Sector ${s.sector ?? "—"} · cell (${s.pos[0]}, ${s.pos[1]})`}
      >
        <div className="d-badges">
          <Badge tone={status === "delivered" ? "good" : status === "reported" ? "critical" : status === "detected" ? "warning" : "neutral"}>
            {SURVIVOR_META[status].label}
          </Badge>
        </div>
        <section className="d-section">
          <div className="eyebrow">Timeline</div>
          <ol className="d-steps">
            {steps.map((step) => (
              <li key={step.label} className={step.done ? "is-done" : ""}>
                <span className="d-step-icon">{step.done ? <CircleCheck size={16} /> : <Circle size={16} />}</span>
                <div>
                  <div className="d-step-label">
                    {step.label}
                    {step.t != null && step.done && <span className="subtle num"> · t={step.t}</span>}
                  </div>
                  {step.note && <div className="subtle d-step-note">{step.note}</div>}
                </div>
              </li>
            ))}
          </ol>
        </section>
        <section className="d-section">
          <div className="eyebrow">Related decisions</div>
          <RelatedLog entries={related} />
        </section>
      </Drawer>
    );
  }
  return null;
}
