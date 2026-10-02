import { memo, useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import { AGENT_META, pct } from "../../lib/meta";
import type { AgentState, Cell, MissionSnapshot, SurvivorState } from "../../lib/types";
import { agentPath, SURVIVOR_META, SurvivorMark, survivorStatus } from "../glyphs";
import "./map.css";

export interface MapLayers {
  links: boolean;
  routes: boolean;
  surveys: boolean;
  labels: boolean;
  truth: boolean;
  ranges: boolean;
}

export type Selection = { type: "agent"; id: string } | { type: "survivor"; id: string } | null;

export interface Placement {
  label: string;
  radius: number;
  color: string;
}

interface Props {
  mission: MissionSnapshot;
  layers: MapLayers;
  selection: Selection;
  onSelect: (s: Selection) => void;
  placement: Placement | null;
  onPlace: (pos: Cell) => void;
  tickSeconds: number;
}

interface Hover {
  x: number;
  y: number;
  content: ReactNode;
}

const dist = (a: Cell, b: Cell) => Math.hypot(a[0] - b[0], a[1] - b[1]);

const Terrain = memo(function Terrain({ terrain }: { terrain: number[][] }) {
  const rects: ReactNode[] = [];
  terrain.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const v = row[x];
      let x2 = x;
      while (x2 + 1 < row.length && row[x2 + 1] === v) x2++;
      if (v !== 0) {
        rects.push(
          <rect
            key={`${x}-${y}`}
            x={x - 0.5}
            y={y - 0.5}
            width={x2 - x + 1}
            height={1}
            className={v === 1 ? "t-water" : "t-building"}
            shapeRendering="crispEdges"
          />,
        );
      }
      x = x2 + 1;
    }
  });
  return <g>{rects}</g>;
});

const DeadZones = memo(function DeadZones({ cells }: { cells: Cell[] }) {
  return (
    <g className="dead-zones">
      {cells.map(([x, y]) => (
        <rect key={`${x}-${y}`} x={x - 0.5} y={y - 0.5} width={1} height={1} shapeRendering="crispEdges" />
      ))}
    </g>
  );
});

export function MissionMap({ mission, layers, selection, onSelect, placement, onPlace, tickSeconds }: Props) {
  const { static: st, state } = mission;
  const W = st.grid.w;
  const H = st.grid.h;
  const svgRef = useRef<SVGSVGElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<Hover | null>(null);
  const [cursor, setCursor] = useState<Cell | null>(null);

  const toCell = useCallback(
    (clientX: number, clientY: number): Cell | null => {
      const svg = svgRef.current;
      if (!svg) return null;
      const pt = svg.createSVGPoint();
      pt.x = clientX;
      pt.y = clientY;
      const m = svg.getScreenCTM();
      if (!m) return null;
      const p = pt.matrixTransform(m.inverse());
      const x = Math.round(p.x);
      const y = Math.round(p.y);
      if (x < 0 || y < 0 || x >= W || y >= H) return null;
      return [x, y];
    },
    [W, H],
  );

  const showTip = (e: React.MouseEvent, content: ReactNode) => {
    const r = stageRef.current?.getBoundingClientRect();
    if (!r) return;
    setHover({ x: e.clientX - r.left, y: e.clientY - r.top, content });
  };

  const display = useMemo(() => {
    const groups = new Map<string, AgentState[]>();
    state.agents.forEach((a) => {
      const k = a.pos.join(",");
      groups.set(k, [...(groups.get(k) ?? []), a]);
    });
    const out = new Map<string, { x: number; y: number; stacked: boolean }>();
    groups.forEach((list) => {
      list.forEach((a, i) => {
        if (list.length === 1) out.set(a.id, { x: a.pos[0], y: a.pos[1], stacked: false });
        else {
          const ang = (i / list.length) * Math.PI * 2 - Math.PI / 2;
          out.set(a.id, { x: a.pos[0] + Math.cos(ang) * 0.85, y: a.pos[1] + Math.sin(ang) * 0.85, stacked: true });
        }
      });
    });
    return out;
  }, [state.agents]);

  const links = useMemo(() => {
    if (!layers.links) return [];
    const fleet = new Map(st.fleet.map((f) => [f.id, f]));
    const nodes: { id: string; pos: Cell; r: number }[] = [{ id: "BASE", pos: st.base, r: st.base_comm }];
    state.agents.forEach((a) => {
      if (a.alive && a.conn) nodes.push({ id: a.id, pos: a.pos, r: fleet.get(a.id)?.comm ?? 6 });
    });
    const out: [Cell, Cell, string][] = [];
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++)
        if (dist(nodes[i].pos, nodes[j].pos) <= Math.max(nodes[i].r, nodes[j].r))
          out.push([nodes[i].pos, nodes[j].pos, `${nodes[i].id}-${nodes[j].id}`]);
    return out;
  }, [layers.links, state.agents, st]);

  const selectedAgent = selection?.type === "agent" ? state.agents.find((a) => a.id === selection.id) : undefined;
  const transition = `transform ${Math.max(0.05, tickSeconds)}s linear`;

  const agentTip = (a: AgentState) => (
    <div className="map-tip">
      <div className="map-tip-title">
        {a.id} <span className="subtle">· {AGENT_META[a.kind].label}</span>
      </div>
      {a.alive ? (
        <>
          <div>{a.activity}</div>
          <div className="subtle num">
            Battery {pct(a.batt)} · {a.conn ? "linked to base" : "no link"}
            {a.kit_cap > 0 && ` · ${a.kits}/${a.kit_cap} kits`}
          </div>
        </>
      ) : (
        <div className="subtle">{a.activity}</div>
      )}
      <div className="map-tip-hint">Click for details</div>
    </div>
  );

  const survivorTip = (s: SurvivorState) => {
    const status = survivorStatus(s);
    return (
      <div className="map-tip">
        <div className="map-tip-title">
          Survivor {s.sid} <span className="subtle">· sector {s.sector ?? "—"}</span>
        </div>
        <div style={{ color: SURVIVOR_META[status].color }}>{SURVIVOR_META[status].label}</div>
        {s.assignee && <div className="subtle">Assigned to {s.assignee}</div>}
        {s.by_call && <div className="subtle">Reported by emergency call</div>}
      </div>
    );
  };

  return (
    <div
      ref={stageRef}
      className={`map-stage ${placement ? "is-placing" : ""}`}
      onMouseLeave={() => {
        setHover(null);
        setCursor(null);
      }}
    >
      <svg
        ref={svgRef}
        className="map-svg"
        viewBox={`-0.5 -0.5 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`Mission map at t=${state.t}`}
        onMouseMove={(e) => placement && setCursor(toCell(e.clientX, e.clientY))}
        onClick={(e) => {
          if (placement) {
            const c = toCell(e.clientX, e.clientY);
            if (c) onPlace(c);
          } else if ((e.target as Element).tagName === "svg" || (e.target as Element).classList.contains("map-bg")) {
            onSelect(null);
          }
        }}
      >
        <defs>
          <pattern id="hatch" width="0.5" height="0.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="0.5" stroke="var(--map-dead)" strokeWidth="0.09" strokeOpacity="0.55" />
          </pattern>
          <radialGradient id="storm-fill">
            <stop offset="0%" stopColor="var(--map-storm)" stopOpacity="0.42" />
            <stop offset="70%" stopColor="var(--map-storm)" stopOpacity="0.2" />
            <stop offset="100%" stopColor="var(--map-storm)" stopOpacity="0.08" />
          </radialGradient>
        </defs>

        <rect className="map-bg" x={-0.5} y={-0.5} width={W} height={H} />
        <Terrain terrain={mission.terrain} />

        {st.bridges.map((cells, i) => {
          const intact = mission.bridges[i];
          const x0 = Math.min(...cells.map((c) => c[0]));
          const y = cells[0][1];
          return (
            <g key={i} className={intact ? "bridge" : "bridge is-down"}>
              <rect x={x0 - 0.5} y={y - 0.32} width={cells.length} height={0.64} rx={0.12} />
              {!intact && layers.labels && (
                <text x={x0 + cells.length / 2 - 0.5} y={y - 0.75} className="map-label tone-critical" textAnchor="middle">
                  {i === 0 ? "North" : "South"} bridge down
                </text>
              )}
            </g>
          );
        })}

        {Object.entries(st.sectors).map(([name, s]) => (
          <g key={name} className="sector">
            <rect x={s.x0 - 0.5} y={s.y0 - 0.5} width={s.x1 - s.x0} height={s.y1 - s.y0} />
            <text x={s.x0 - 0.1} y={s.y0 + 0.35} className="sector-label">
              SECTOR {name}
            </text>
          </g>
        ))}

        <DeadZones cells={mission.dead} />

        {state.storm && (
          <g className="storm">
            <circle cx={state.storm.cx} cy={state.storm.cy} r={state.storm.r} fill="url(#storm-fill)" />
            <circle cx={state.storm.cx} cy={state.storm.cy} r={state.storm.r} className="storm-edge" />
            {layers.labels && (
              <text x={state.storm.cx} y={Math.min(H - 1, state.storm.cy + state.storm.r + 0.95)} className="map-label storm-label" textAnchor="middle">
                Storm cell · clears t={state.storm.t_end}
              </text>
            )}
          </g>
        )}

        {layers.ranges && (
          <g className="ranges">
            <circle cx={st.base[0]} cy={st.base[1]} r={st.base_comm} />
            {state.agents
              .filter((a) => a.alive && a.kind === "relay")
              .map((a) => (
                <circle key={a.id} cx={a.pos[0]} cy={a.pos[1]} r={st.fleet.find((f) => f.id === a.id)?.comm ?? 16} />
              ))}
          </g>
        )}

        {layers.surveys &&
          state.surveys.map((s) => (
            <circle
              key={s.id}
              cx={s.pos[0]}
              cy={s.pos[1]}
              r={s.status === "done" ? 0.2 : 0.22}
              className={`waypoint wp-${s.status}`}
              onMouseMove={(e) =>
                showTip(
                  e,
                  <div className="map-tip">
                    <div className="map-tip-title">{mission.labels[s.id] ?? s.id}</div>
                    <div className="subtle">
                      {s.status === "done" ? "Surveyed" : s.status === "void" ? "Not in mission scope" : s.assignee ? `Assigned to ${s.assignee}` : "Unassigned"}
                    </div>
                  </div>,
                )
              }
              onMouseLeave={() => setHover(null)}
            />
          ))}

        {layers.links && (
          <g className="links">
            {links.map(([a, b, k]) => (
              <line key={k} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />
            ))}
          </g>
        )}

        {layers.routes &&
          state.agents
            .filter((a) => a.alive && a.route.length)
            .map((a) => (
              <polyline
                key={a.id}
                className={`route ${selectedAgent && selectedAgent.id !== a.id ? "is-dim" : ""} ${selectedAgent?.id === a.id ? "is-focus" : ""}`}
                points={[a.pos, ...a.route].map((p) => p.join(",")).join(" ")}
                stroke={AGENT_META[a.kind].color}
              />
            ))}

        <g className="base" transform={`translate(${st.base[0]} ${st.base[1]})`}>
          <path d="M0 -0.95 L0.82 -0.47 L0.82 0.47 L0 0.95 L-0.82 0.47 L-0.82 -0.47 Z" />
          <text y={1.85} className="map-label base-label" textAnchor="middle">
            BASE
          </text>
        </g>

        {state.survivors.map((s) => {
          const status = survivorStatus(s);
          if (status === "hidden" && !layers.truth) return null;
          const sel = selection?.type === "survivor" && selection.id === s.sid;
          return (
            <g
              key={s.sid}
              className={`survivor ${sel ? "is-selected" : ""} ${status === "reported" ? "is-urgent" : ""}`}
              transform={`translate(${s.pos[0]} ${s.pos[1]})`}
              onMouseMove={(e) => showTip(e, survivorTip(s))}
              onMouseLeave={() => setHover(null)}
              onClick={(e) => {
                e.stopPropagation();
                if (!placement) onSelect({ type: "survivor", id: s.sid });
              }}
            >
              <circle r={1.1} className="hit" />
              {status === "reported" && <circle r={0.9} className="urgent-ring" />}
              {sel && <circle r={1.05} className="sel-ring" />}
              <SurvivorMark status={status} />
              {status !== "hidden" && layers.labels && (
                <text x={0.85} y={-0.55} className="map-label survivor-label">
                  {s.sid}
                </text>
              )}
            </g>
          );
        })}

        {state.agents.map((a) => {
          const d = display.get(a.id)!;
          const sel = selectedAgent?.id === a.id;
          const flip = d.x > W - 9;
          const showLabel = layers.labels && (!d.stacked || sel);
          return (
            <g
              key={a.id}
              className={`agent ${a.alive ? "" : "is-lost"} ${sel ? "is-selected" : ""}`}
              style={{ transform: `translate(${d.x}px, ${d.y}px)`, transition }}
              onMouseMove={(e) => showTip(e, agentTip(a))}
              onMouseLeave={() => setHover(null)}
              onClick={(e) => {
                e.stopPropagation();
                if (!placement) onSelect({ type: "agent", id: a.id });
              }}
            >
              <circle r={1.15} className="hit" />
              {sel && <circle r={1.25} className="sel-ring" />}
              {a.alive && a.storm_exposed && <circle r={1.0} className="storm-ring" />}
              {a.alive && !a.conn && <circle r={0.95} className="nolink-ring" />}
              {a.alive ? (
                <path d={agentPath(a.kind, 0.58)} fill={AGENT_META[a.kind].color} className="agent-mark" />
              ) : (
                <path d="M-0.45 -0.45 L0.45 0.45 M0.45 -0.45 L-0.45 0.45" className="lost-mark" />
              )}
              {showLabel && (
                <text x={flip ? -0.95 : 0.95} y={-0.55} textAnchor={flip ? "end" : "start"} className="map-label agent-label">
                  {a.id}
                  <tspan className={`agent-batt batt-${a.alive ? (a.batt > 0.45 ? "ok" : a.batt > 0.25 ? "low" : "crit") : "lost"}`}>
                    {a.alive ? ` ${Math.round(a.batt * 100)}%` : " lost"}
                  </tspan>
                </text>
              )}
            </g>
          );
        })}

        {placement && cursor && (
          <g className="placement" transform={`translate(${cursor[0]} ${cursor[1]})`}>
            <circle r={Math.max(placement.radius, 0.7)} style={{ stroke: placement.color, fill: placement.color }} />
            <circle r={0.18} style={{ fill: placement.color }} />
          </g>
        )}
      </svg>

      {hover && !placement && (
        <div
          className="map-tooltip"
          style={{
            left: hover.x,
            top: hover.y,
            transform: `translate(${hover.x > (stageRef.current?.clientWidth ?? 0) - 240 ? "calc(-100% - 14px)" : "14px"}, -50%)`,
          }}
        >
          {hover.content}
        </div>
      )}
    </div>
  );
}
