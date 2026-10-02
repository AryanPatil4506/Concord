// Figures not in results/summary.json, from the research dossier §4.

export type Policy = "concord" | "greedy" | "static";
export type Triple = [number, number, number]; // mean, CI low, CI high

export const POLICIES: { id: Policy; name: string; color: string; blurb: string }[] = [
  { id: "concord", name: "CONCORD", color: "var(--policy-concord)", blurb: "Auction with time-discounted bids, risk-aware routing, VoI messaging, relay repositioning, hysteresis" },
  { id: "greedy", name: "Greedy dispatch", color: "var(--policy-greedy)", blurb: "Nearest open task to each idle capable agent; same smart return-to-home" },
  { id: "static", name: "Static plan", color: "var(--policy-static)", blurb: "One-shot allocation at t=0; no re-allocation after failures" },
];

export const DOSSIER_EXTRA = {
  median_tta: { concord: 59, greedy: 66, static: 157 },
  within_120: { concord: 0.933, greedy: 0.882, static: 0.418 },
  wall_ms: { concord: 131, greedy: 31, static: 38 },
  survivors: 1676,
  scenarios: 300,
  missions: 4500,
};

export const SCALING = [
  { agents: 5, tasks: 15, repair: 0.16, global: 0.8, cold: 68 },
  { agents: 10, tasks: 30, repair: 0.49, global: 4.7, cold: 170 },
  { agents: 20, tasks: 60, repair: 0.8, global: 16.6, cold: 307 },
  { agents: 50, tasks: 150, repair: 1.96, global: 131, cold: 620 },
  { agents: 100, tasks: 300, repair: 4.06, global: 611, cold: 1270 },
  { agents: 200, tasks: 600, repair: 8.56, global: 2360, cold: 2120 },
];

export const ABLATIONS: { id: string; label: string; readout: string }[] = [
  { id: "full", label: "Full CONCORD", readout: "Reference" },
  { id: "no_voi_messaging", label: "− value-of-information messaging", readout: "Biggest lever on awareness: critical reports arrive 5.2× later without it." },
  { id: "no_hysteresis", label: "− hysteresis", readout: "Hysteresis buys 33× plan stability for ~8% energy." },
  { id: "no_risk_awareness", label: "− risk-aware routing", readout: "Biggest safety lever: 1.75× more avoidable losses without it." },
  { id: "no_relay_repositioning", label: "− relay repositioning", readout: "Trims report latency by about a quarter." },
  { id: "no_battery_invariant", label: "− battery-reserve invariant", readout: "No measurable effect in v0 — smart return-to-home already catches most cases." },
];

export const LIMITS = [
  "Grid world, abstract agents, no physics — by design (the PS asks for mission-level autonomy), but still a simulation.",
  "The auction is centralised while agents are connected; decentralised CBBA consensus is on the build plan.",
  "The forecaster samples future disruptions from the same prior the benchmark uses, so its calibration is optimistic by construction.",
  "The battery-reserve invariant shows no measurable benefit in v0 because smart return-to-home already catches most cases.",
  "1 tick ≈ 10 s is an interpretation, not a calibrated constant — all claims are in ticks.",
  "Escalations were measured only in the storyboard mission, not across the benchmark.",
];

export interface EvidenceData {
  main: Record<Policy, Record<string, Triple | number>>;
  stress: Record<string, Record<Policy, Record<string, Triple | number>>>;
  ablation: Record<string, Record<string, Triple | number>>;
  paired: Record<string, Triple>;
  storyboard?: { metrics: Record<string, unknown>; timeline: [number, number][] };
}

export const tri = (v: Triple | number | undefined): Triple => (Array.isArray(v) ? v : [v ?? 0, v ?? 0, v ?? 0]);
