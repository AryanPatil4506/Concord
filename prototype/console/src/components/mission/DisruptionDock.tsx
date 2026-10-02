import { useNow } from "../../lib/hooks";
import { DISRUPTIONS, pct } from "../../lib/meta";
import type { AgentState, DisruptionKind } from "../../lib/types";
import { AgentGlyph } from "../glyphs";
import { Popover, Tooltip } from "../ui/ui";
import "./dock.css";

interface Props {
  agents: AgentState[];
  bridges: boolean[];
  stormActive: boolean;
  disabledReason: string | null;
  lastInjectAt: number;
  cooldownS: number;
  placing: DisruptionKind | null;
  onPlace: (kind: DisruptionKind | null) => void;
  onInject: (kind: DisruptionKind, params?: Record<string, unknown>) => void;
}

export function DisruptionDock({
  agents,
  bridges,
  stormActive,
  disabledReason,
  lastInjectAt,
  cooldownS,
  placing,
  onPlace,
  onInject,
}: Props) {
  const now = useNow(Date.now() - lastInjectAt < cooldownS * 1000 + 300, 100);
  const cooling = Math.max(0, 1 - (now - lastInjectAt) / (cooldownS * 1000));
  const blocked = disabledReason ?? (cooling > 0 ? "One disruption every 2 seconds" : null);

  return (
    <div className="dock" role="toolbar" aria-label="Inject a disruption">
      <div className="dock-label">
        <span className="eyebrow">Break the plan</span>
        {cooling > 0 && <span className="dock-cool" style={{ transform: `scaleX(${cooling})` }} />}
      </div>
      <div className="dock-buttons">
        {DISRUPTIONS.map((d) => {
          const Icon = d.icon;
          const extraBlock =
            d.kind === "storm" && stormActive
              ? "A storm cell is already active"
              : d.kind === "bridge_collapse" && !bridges.some(Boolean)
                ? "Both bridges are down"
                : null;
          const why = blocked ?? extraBlock;
          const btn = (open?: boolean, toggle?: () => void) => {
            const button = (
              <button
                className={`dock-btn ${placing === d.kind || open ? "is-active" : ""}`}
                disabled={!!why}
                onClick={() => {
                  if (d.target === "place") onPlace(placing === d.kind ? null : d.kind);
                  else toggle?.();
                }}
              >
                <Icon />
                <span>{d.short}</span>
              </button>
            );
            return open ? button : (
              <Tooltip content={why ?? d.hint} side="top" className="tt-wide">
                {button}
              </Tooltip>
            );
          };
          if (d.target === "place") return <div key={d.kind}>{btn()}</div>;
          return (
            <Popover key={d.kind} side="top" align="center" trigger={({ open, toggle }) => btn(open, toggle)}>
              {(close) => (
                <div role="menu">
                  <div className="menu-label eyebrow">{d.label}</div>
                  {d.target === "agent" &&
                    agents.map((a) => (
                      <button
                        key={a.id}
                        role="menuitem"
                        className="menu-item"
                        disabled={!a.alive}
                        onClick={() => {
                          onInject(d.kind, { agent: a.id });
                          close();
                        }}
                      >
                        <AgentGlyph kind={a.kind} lost={!a.alive} />
                        {a.id}
                        <span className="menu-meta num">{a.alive ? pct(a.batt) : "lost"}</span>
                      </button>
                    ))}
                  {d.target === "bridge" &&
                    ["North bridge", "South bridge"].map((name, i) => (
                      <button
                        key={name}
                        role="menuitem"
                        className="menu-item"
                        disabled={!bridges[i]}
                        onClick={() => {
                          onInject(d.kind, { bridge: i });
                          close();
                        }}
                      >
                        {name}
                        <span className="menu-meta">{bridges[i] ? "intact" : "down"}</span>
                      </button>
                    ))}
                </div>
              )}
            </Popover>
          );
        })}
      </div>
    </div>
  );
}
