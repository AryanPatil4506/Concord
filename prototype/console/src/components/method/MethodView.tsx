import { Activity, AlertTriangle, FileCode2, Gavel, RadioTower, RefreshCcw } from "lucide-react";
import { AGENT_META } from "../../lib/meta";
import type { AgentKind } from "../../lib/types";
import { AgentGlyph } from "../glyphs";
import "../evidence/evidence.css";
import "./method.css";

const LOOP = [
  { icon: FileCode2, title: "Compile intent", body: "Plain-English objective → schema-checked Mission DAG. Validated against map and fleet; a human confirms.", who: "LLM translates · human confirms" },
  { icon: Gavel, title: "Allocate", body: "CBBA-style sequential auction with time-discounted bids, energy and storm-risk penalties, and a battery-reserve invariant.", who: "Algorithm" },
  { icon: RadioTower, title: "Stay connected", body: "Relay repositions every 5 ticks; critical reports outrank telemetry; scouts detour to report from dead zones.", who: "Algorithm" },
  { icon: RefreshCcw, title: "Repair or re-plan", body: "Local repair auctions on events; global re-plan on storms, bridge loss and every 30 ticks, with hysteresis against churn.", who: "Algorithm" },
  { icon: Activity, title: "Forecast", body: "40 Monte-Carlo rollouts of the live plan, future disruptions sampled from the prior → P(mission success).", who: "Algorithm" },
  { icon: AlertTriangle, title: "Escalate", body: "Below 60% (or for irreversible calls) the operator gets a card with odds per option; a safe default runs on timeout.", who: "Human owns the call" },
];

const ALIGN = [
  ["Convert high-level objectives into coordinated tasks, dependencies, priorities", "Mission compiler → typed Mission DAG (LLM + schema + human confirm)"],
  ["Allocate by capability, location, battery, payload, comms, risk, priority", "CBBA-style auction with time-discounted bids + battery-reserve invariant"],
  ["Re-plan on failures, obstacles, environment, new info, priorities", "Event-driven repair vs global re-plan with hysteresis"],
  ["Communication-aware; decide what's worth transmitting", "Relay repositioning, value-of-information queue, report-seeking detour, disconnected autonomy"],
  ["Identify when the mission is no longer safely achievable; escalate", "Monte-Carlo feasibility forecast → escalation card with P(success) per option"],
  ["≥ 3 heterogeneous agents", "4 agent types: scout drone ×2, cargo drone, rover (UGV), relay drone"],
  ["Explanations for major autonomous decisions", "Structured decision log rendered as one-line reasons, with bid tables"],
];

const FLEET: { kind: AgentKind; count: number; caps: string; speed: string; battery: number; comm: number; notes: string }[] = [
  { kind: "scout", count: 2, caps: "camera", speed: "2.0", battery: 110, comm: 7, notes: "Fast, short battery, weather-sensitive" },
  { kind: "cargo", count: 1, caps: "payload · 1 kit", speed: "1.5", battery: 120, comm: 7, notes: "Fast delivery, reloads at base each trip" },
  { kind: "rover", count: 1, caps: "payload · 3 kits", speed: "1.0", battery: 500, comm: 6, notes: "Slow, robust, terrain-bound (bridges)" },
  { kind: "relay", count: 1, caps: "relay", speed: "1.5", battery: 220, comm: 16, notes: "Extends the base link" },
];

const PRIOR = [
  ["Agent hardware failure", "0.6", "40–200"],
  ["Sudden battery drain (−45%)", "0.6", "40–200"],
  ["Bridge collapse", "0.5", "30–180"],
  ["Comm blackout (r = 4)", "0.5", "30–180"],
  ["Storm cell (r = 5.5, 70 ticks)", "0.5", "40–170"],
  ["Emergency call (new survivor)", "0.6", "40–220"],
];

const PARAMS = [
  ["τ", "120", "time discount — earlier completion bids higher"],
  ["β", "0.05", "energy penalty (fraction of capacity)"],
  ["γ", "1.0", "storm-risk penalty"],
  ["δ", "0.08", "stickiness — keeps the current owner (hysteresis)"],
  ["risk ceiling", "0.12", "tasks riskier than this wait or go to ground agents"],
  ["max bundle", "6", "tasks per agent per auction"],
  ["reserve", "×1.15 + 5", "battery to finish, return and keep a margin"],
];

export function MethodView() {
  return (
    <div className="ev method">
      <header className="ev-hero">
        <div className="eyebrow">How CONCORD decides</div>
        <h1>LLMs understand intent. Algorithms make decisions. Humans own the hard calls.</h1>
        <p className="muted">
          Every robot is an abstract agent — position, speed, battery, sensors, payload, radio range. CONCORD is the mission brain above them: it
          never flies a drone, it decides who does what, re-plans when the world changes, and knows when to ask.
        </p>
      </header>

      <section className="ev-section">
        <div className="loop">
          {LOOP.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.title} className={`loop-step ${s.who.startsWith("Human") ? "is-human" : ""}`}>
                <div className="loop-top">
                  <span className="loop-n num">{i + 1}</span>
                  <Icon />
                </div>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
                <span className="loop-who">{s.who}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="ev-section">
        <header className="ev-section-head">
          <div>
            <div className="ev-kicker">Problem statement EL-05</div>
            <h2>Every objective has a component</h2>
          </div>
        </header>
        <div className="ev-card ev-table-wrap">
          <table className="ev-table">
            <thead>
              <tr>
                <th>PS objective / deliverable</th>
                <th>CONCORD component</th>
              </tr>
            </thead>
            <tbody>
              {ALIGN.map(([a, b]) => (
                <tr key={a}>
                  <td>{a}</td>
                  <td className="method-wrap">{b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="ev-section">
        <header className="ev-section-head">
          <div>
            <div className="ev-kicker">Allocation</div>
            <h2>The bid</h2>
          </div>
        </header>
        <div className="method-two">
          <div className="ev-card">
            <div className="formula" aria-label="score equals priority times e to the minus t over tau, minus beta times energy over capacity, minus gamma times risk, plus delta if sticky">
              score = <em>p</em>·e<sup>−t/τ</sup> − β·<em>E</em>/<em>E</em><sub>cap</sub> − γ·<em>risk</em> + δ·[current owner]
            </div>
            <p className="muted method-p">
              The auction repeatedly awards the single highest (agent, task) bid and re-bids only that agent (lazy max-heap), so a global re-plan costs
              O(A·T + T²) bid evaluations. A bid only exists if the agent has the capability, can reach the task, and still satisfies the battery
              reserve afterwards — optionally via a recharge/reload stop at base.
            </p>
          </div>
          <div className="ev-card ev-table-wrap">
            <table className="ev-table">
              <tbody>
                {PARAMS.map(([k, v, d]) => (
                  <tr key={k}>
                    <td className="mono">{k}</td>
                    <td className="num">{v}</td>
                    <td className="method-wrap">{d}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="ev-section">
        <header className="ev-section-head">
          <div>
            <div className="ev-kicker">World</div>
            <h2>Fleet and disruptions</h2>
          </div>
        </header>
        <div className="ev-card ev-table-wrap">
          <table className="ev-table">
            <thead>
              <tr>
                <th>Agent</th>
                <th className="r">Count</th>
                <th>Capabilities</th>
                <th className="r">Speed</th>
                <th className="r">Battery</th>
                <th className="r">Radio</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {FLEET.map((f) => (
                <tr key={f.kind}>
                  <td>
                    <span className="method-agent">
                      <AgentGlyph kind={f.kind} /> {AGENT_META[f.kind].label}
                    </span>
                  </td>
                  <td className="r num">{f.count}</td>
                  <td>{f.caps}</td>
                  <td className="r num">{f.speed}</td>
                  <td className="r num">{f.battery}</td>
                  <td className="r num">{f.comm}</td>
                  <td className="method-wrap">{f.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="method-two">
          <div className="ev-card ev-table-wrap">
            <table className="ev-table">
              <thead>
                <tr>
                  <th>Disruption (benchmark prior)</th>
                  <th className="r">P(occurs)</th>
                  <th className="r">Window (ticks)</th>
                </tr>
              </thead>
              <tbody>
                {PRIOR.map(([a, b, c]) => (
                  <tr key={a}>
                    <td>{a}</td>
                    <td className="r num">{b}</td>
                    <td className="r num">{c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="ev-card">
            <h3 className="method-h3">The world</h3>
            <ul className="method-list">
              <li>40 × 28 grid (≈ 2 × 1.4 km at 50 m per cell); base on the west bank; a river with two bridges; three flood pockets; buildings block ground agents.</li>
              <li>Four survey sectors A–D east of the river, 24 waypoints; scouts detect survivors within 2 cells.</li>
              <li>Comms: link if distance ≤ max(range); mesh by BFS; dead zones block links; 2 messages uplinked per tick.</li>
              <li>Storm: drones inside fly at half speed and are lost with probability 0.04 per tick.</li>
              <li>Success = every survivor has a med-kit before the horizon.</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
