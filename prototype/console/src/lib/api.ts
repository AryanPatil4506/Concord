import type { CompiledMission, ScenarioInfo } from "./types";

/** Static build for hosting without the engine: missions replay recordings made by `record_demo.py`. */
export const DEMO = import.meta.env.VITE_DEMO === "1";

const json = async <T,>(url: string, init?: RequestInit): Promise<T> => {
  const r = await fetch(url, init);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json() as Promise<T>;
};

export type DemoScenario = ScenarioInfo & { tmax: number };

let demoScenarios: Promise<DemoScenario[]> | null = null;
export const loadDemoScenarios = () => (demoScenarios ??= json<DemoScenario[]>("/demo/scenarios.json"));

export const getScenarios = (): Promise<ScenarioInfo[]> => (DEMO ? loadDemoScenarios() : json("/api/scenarios"));

export const getDefaultObjective = async (): Promise<string> =>
  DEMO ? DEFAULT_OBJECTIVE : (await json<{ text: string }>("/api/default-objective")).text;

export const getEvidence = <T,>(): Promise<T> => json<T>(DEMO ? "/demo/evidence.json" : "/api/evidence");

export async function compileObjective(text: string, scenario: string): Promise<CompiledMission> {
  if (!DEMO)
    return json("/api/compile", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, scenario }),
    });
  const sc = (await loadDemoScenarios()).find((s) => s.id === scenario);
  return compile(text, sc?.tmax ?? 200);
}

// ---- port of server/compiler.py (rule-based, no LLM) ----

const DEFAULT_OBJECTIVE =
  "Flood response east of the river: survey sectors A to D, find everyone who is trapped " +
  "and get a med-kit to each survivor as fast as possible. Keep every agent linked to base " +
  "and don't lose drones to the weather.";

const T_MAX = 320;
const SECTORS = ["A", "B", "C", "D"];
const FLEET_CAPS: Record<string, string[]> = {
  camera: ["Scout-1", "Scout-2"],
  payload: ["Cargo-1", "Rover-1"],
  relay: ["Relay-1"],
};

function sectorsOf(text: string): string[] {
  const t = text.toUpperCase();
  const m = t.match(/SECTORS?\s+([A-D])\s*(?:-|–|TO|THROUGH)\s*([A-D])/);
  if (m) {
    const [a, b] = [m[1], m[2]].sort();
    const out: string[] = [];
    for (let c = a.charCodeAt(0); c <= b.charCodeAt(0); c++) out.push(String.fromCharCode(c));
    return out;
  }
  const found = [...t.matchAll(/(?:SECTORS?|,|AND)\s+([A-D])\b/g)].map((x) => x[1]);
  const uniq = [...new Set(found)].sort();
  return uniq.length ? uniq : [...SECTORS];
}

function compile(raw: string, tmax: number, nWaypoints = 6): CompiledMission {
  const text = raw.trim() || DEFAULT_OBJECTIVE;
  const low = text.toLowerCase();
  const sectors = sectorsOf(text);
  const has = (ks: string[]) => ks.some((k) => low.includes(k));
  const wantsDelivery = has(["med", "kit", "deliver", "supplies", "aid"]);
  const wantsLink = has(["link", "comm", "connected", "contact"]);
  const riskAverse = has(["weather", "storm", "don't lose", "do not lose", "safe"]);
  const m = low.match(/within\s+(\d+)\s*(ticks?|min(?:ute)?s?)/);
  let horizon = tmax;
  if (m) horizon = m[2].startsWith("tick") ? Number(m[1]) : Number(m[1]) * 6; // 1 tick ≈ 10 s

  const nodes: CompiledMission["nodes"] = [];
  const edges: [string, string][] = [];
  for (const s of sectors) {
    nodes.push({ id: `survey-${s}`, type: "survey", label: `Survey sector ${s}`, detail: `${nWaypoints} waypoints · camera`, requires: "camera", priority: 0.4, sector: s });
    edges.push([`survey-${s}`, "locate"]);
  }
  nodes.push({ id: "locate", type: "locate", label: "Locate survivors", detail: "Camera, 2-cell radius · critical report", requires: "camera", priority: 1.0 });
  if (wantsDelivery) {
    nodes.push({ id: "deliver", type: "deliver", label: "Deliver med-kits", detail: "1 per reported survivor · payload", requires: "payload", priority: 1.0 });
    edges.push(["locate", "deliver"]);
  }
  nodes.push({ id: "link", type: "relay", label: "Maintain link to base", detail: "Relay repositioning · value-of-information messaging", requires: "relay", priority: 0.6, continuous: true });

  const constraints = [
    { label: "Mission horizon", value: `${horizon} ticks (≈ ${Math.floor((horizon * 10) / 60)} min at 1 tick ≈ 10 s)` },
    { label: "Battery reserve", value: "Finish + return ×1.15 + 5 units on every bid" },
    { label: "Storm-risk ceiling", value: "0.12 per task" + (riskAverse ? " · weather flagged by operator" : "") },
    { label: "Escalate to operator", value: "P(success) < 60% or irreversible action" },
  ];
  if (wantsLink) constraints.push({ label: "Comms", value: "Keep agents linked; critical reports outrank telemetry" });
  const checks = [
    { label: "All referenced sectors exist on the map", ok: sectors.every((s) => SECTORS.includes(s)) },
    { label: "Every task has a capable agent", ok: nodes.every((n) => n.requires in FLEET_CAPS) },
    { label: "Task graph is acyclic", ok: true },
    { label: "Horizon fits the scenario", ok: horizon <= Math.max(tmax, T_MAX) },
  ];
  return {
    objective: text,
    compiler: "offline rule-based fallback (no LLM)",
    sectors,
    horizon,
    nodes,
    edges,
    constraints,
    checks,
    capabilities: FLEET_CAPS,
    task_count: sectors.length * nWaypoints,
  };
}
