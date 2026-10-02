import { CloudLightning, Package, Users, Wifi, WifiOff } from "lucide-react";
import { AGENT_META, batteryTone } from "../../lib/meta";
import type { AgentState } from "../../lib/types";
import { AgentGlyph } from "../glyphs";
import { Meter, SectionHeader, Tooltip } from "../ui/ui";
import "./swarm.css";

export function SwarmPanel({
  agents,
  selected,
  onSelect,
}: {
  agents: AgentState[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const up = agents.filter((a) => a.alive).length;
  return (
    <section className="panel" aria-label="Swarm">
      <SectionHeader
        title="Swarm"
        icon={<Users />}
        info="Five heterogeneous agents. Shape and colour identify the type; click a row (or the agent on the map) for its plan, specs and actions."
        actions={<span className="subtle num swarm-count">{up}/{agents.length} operational</span>}
      />
      <ul className="swarm-list">
        {agents.map((a) => (
          <li key={a.id}>
            <button
              className={`swarm-row ${a.alive ? "" : "is-lost"} ${selected === a.id ? "is-selected" : ""}`}
              onClick={() => onSelect(a.id)}
            >
              <span className="swarm-glyph">
                <AgentGlyph kind={a.kind} size={16} lost={!a.alive} title={AGENT_META[a.kind].label} />
              </span>
              <span className="swarm-main">
                <span className="swarm-name">
                  {a.id}
                  {a.alive && a.storm_exposed && (
                    <Tooltip content="Inside the storm cell">
                      <CloudLightning className="swarm-flag flag-storm" aria-label="In storm" />
                    </Tooltip>
                  )}
                  {a.alive && a.queued_critical > 0 && (
                    <Tooltip content={`${a.queued_critical} critical report queued`}>
                      <span className="swarm-flag-dot" aria-label="Critical report queued" />
                    </Tooltip>
                  )}
                </span>
                <span className="swarm-activity">{a.activity}</span>
              </span>
              <span className="swarm-side">
                {a.alive ? (
                  <>
                    <span className="swarm-batt">
                      <Meter value={a.batt} tone={batteryTone(a.batt)} height={4} label={`${a.id} battery`} />
                      <span className="num">{Math.round(a.batt * 100)}%</span>
                    </span>
                    <span className="swarm-status">
                      {a.kit_cap > 0 && (
                        <span className="swarm-kits num" title={`${a.kits} of ${a.kit_cap} med-kits on board`}>
                          <Package /> {a.kits}/{a.kit_cap}
                        </span>
                      )}
                      {a.conn ? (
                        <span className="link-ok">
                          <Wifi /> Linked
                        </span>
                      ) : (
                        <span className="link-bad">
                          <WifiOff /> No link
                        </span>
                      )}
                    </span>
                  </>
                ) : (
                  <span className="lost-tag">Lost</span>
                )}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
