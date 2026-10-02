import { Layers, ListTree } from "lucide-react";
import type { ReactNode } from "react";
import { AGENT_META } from "../../lib/meta";
import type { AgentKind } from "../../lib/types";
import { AgentGlyph, SURVIVOR_META, SurvivorGlyph, type SurvivorStatus } from "../glyphs";
import type { MapLayers } from "../map/MissionMap";
import { Popover } from "../ui/ui";
import "./mapcontrols.css";

const LAYER_LABELS: { key: keyof MapLayers; label: string; hint: string }[] = [
  { key: "labels", label: "Labels", hint: "Agent names, battery and survivor IDs" },
  { key: "routes", label: "Planned routes", hint: "Next waypoints of every agent's bundle" },
  { key: "links", label: "Comm links", hint: "Mesh links between base and linked agents" },
  { key: "ranges", label: "Comm ranges", hint: "Base (14) and relay (16) radio range" },
  { key: "surveys", label: "Survey waypoints", hint: "24 camera waypoints in sectors A–D" },
  { key: "truth", label: "Ground truth", hint: "Show survivors the swarm hasn't found yet (simulation only)" },
];

export function LayerMenu({ layers, onChange }: { layers: MapLayers; onChange: (l: MapLayers) => void }) {
  return (
    <Popover
      side="bottom"
      align="end"
      trigger={({ open, toggle }) => (
        <button className={`map-ctl ${open ? "is-active" : ""}`} onClick={toggle} aria-haspopup="menu" aria-expanded={open}>
          <Layers /> Layers
        </button>
      )}
    >
      {() => (
        <div className="layer-menu" role="menu">
          {LAYER_LABELS.map((l) => (
            <label key={l.key} className="layer-row">
              <input
                type="checkbox"
                checked={layers[l.key]}
                onChange={(e) => onChange({ ...layers, [l.key]: e.target.checked })}
              />
              <span className="switch" aria-hidden />
              <span className="layer-text">
                <span>{l.label}</span>
                <span className="subtle">{l.hint}</span>
              </span>
            </label>
          ))}
        </div>
      )}
    </Popover>
  );
}

function Key({ mark, label }: { mark: ReactNode; label: string }) {
  return (
    <li>
      <span className="legend-mark">{mark}</span>
      {label}
    </li>
  );
}

export function Legend() {
  return (
    <Popover
      side="bottom"
      align="end"
      trigger={({ open, toggle }) => (
        <button className={`map-ctl ${open ? "is-active" : ""}`} onClick={toggle} aria-expanded={open}>
          <ListTree /> Legend
        </button>
      )}
    >
      {() => (
        <div className="legend">
          <div className="legend-group">
            <div className="eyebrow">Agents</div>
            <ul>
              {(Object.keys(AGENT_META) as AgentKind[]).map((k) => (
                <Key key={k} mark={<AgentGlyph kind={k} />} label={AGENT_META[k].label} />
              ))}
              <Key mark={<span className="lg-ring lg-nolink" />} label="No link to base" />
              <Key mark={<span className="lg-x">✕</span>} label="Agent lost" />
            </ul>
          </div>
          <div className="legend-group">
            <div className="eyebrow">Survivors</div>
            <ul>
              {(["detected", "reported", "delivered", "hidden"] as SurvivorStatus[]).map((s) => (
                <Key key={s} mark={<SurvivorGlyph status={s} />} label={SURVIVOR_META[s].label} />
              ))}
            </ul>
          </div>
          <div className="legend-group">
            <div className="eyebrow">Map</div>
            <ul>
              <Key mark={<span className="lg-sw lg-water" />} label="River / flood water" />
              <Key mark={<span className="lg-sw lg-building" />} label="Building (ground-impassable)" />
              <Key mark={<span className="lg-sw lg-bridge" />} label="Bridge" />
              <Key mark={<span className="lg-sw lg-dead" />} label="Comm dead zone" />
              <Key mark={<span className="lg-ring lg-storm" />} label="Storm cell (aerial hazard)" />
              <Key mark={<span className="lg-line" />} label="Comm link" />
              <Key mark={<span className="lg-dash" />} label="Planned route" />
              <Key mark={<span className="lg-wp" />} label="Survey waypoint (filled = done)" />
            </ul>
          </div>
        </div>
      )}
    </Popover>
  );
}
