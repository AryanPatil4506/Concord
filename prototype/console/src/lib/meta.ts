import {
  AlertTriangle,
  BatteryLow,
  BatteryWarning,
  CloudLightning,
  Eye,
  Inbox,
  PackageCheck,
  PhoneCall,
  Radio,
  RadioTower,
  Send,
  Shuffle,
  Split,
  UserCheck,
  WifiOff,
  XOctagon,
  Zap,
  Construction,
  type LucideIcon,
} from "lucide-react";
import type { AgentKind, DisruptionKind, LogKind } from "./types";

export const AGENT_META: Record<AgentKind, { label: string; color: string; shape: string; role: string }> = {
  scout: { label: "Scout drone", color: "var(--agent-scout)", shape: "Triangle", role: "Camera · finds survivors" },
  cargo: { label: "Cargo drone", color: "var(--agent-cargo)", shape: "Inverted triangle", role: "Carries 1 med-kit · fast" },
  rover: { label: "Rover (UGV)", color: "var(--agent-rover)", shape: "Square", role: "Carries 3 med-kits · ground" },
  relay: { label: "Relay drone", color: "var(--agent-relay)", shape: "Diamond", role: "Extends the base link" },
};

export type LogCategory = "disruption" | "allocation" | "comms" | "safety" | "rescue" | "human";

export const LOG_META: Record<LogKind, { icon: LucideIcon; tone: string; category: LogCategory; label: string }> = {
  event: { icon: Zap, tone: "warning", category: "disruption", label: "Disruption" },
  relay: { icon: RadioTower, tone: "neutral", category: "comms", label: "Relay" },
  replan: { icon: Shuffle, tone: "accent", category: "allocation", label: "Re-plan" },
  assign: { icon: Split, tone: "accent", category: "allocation", label: "Auction" },
  battery: { icon: BatteryWarning, tone: "serious", category: "safety", label: "Battery reserve" },
  voi: { icon: Send, tone: "neutral", category: "comms", label: "Value of information" },
  detect: { icon: Eye, tone: "neutral", category: "rescue", label: "Detection" },
  report: { icon: Inbox, tone: "neutral", category: "comms", label: "Report" },
  deliver: { icon: PackageCheck, tone: "good", category: "rescue", label: "Aid delivered" },
  loss: { icon: XOctagon, tone: "critical", category: "safety", label: "Asset lost" },
  escalation: { icon: AlertTriangle, tone: "warning", category: "human", label: "Escalation" },
  operator: { icon: UserCheck, tone: "accent", category: "human", label: "Operator" },
};

export const LOG_FILTERS: { id: LogCategory | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "disruption", label: "Disruptions" },
  { id: "allocation", label: "Allocation" },
  { id: "comms", label: "Comms" },
  { id: "safety", label: "Safety" },
  { id: "rescue", label: "Rescue" },
  { id: "human", label: "Human" },
];

export type DisruptionTarget = "agent" | "place" | "bridge";

export const DISRUPTIONS: {
  kind: DisruptionKind;
  label: string;
  short: string;
  icon: LucideIcon;
  target: DisruptionTarget;
  hint: string;
  radius?: number;
}[] = [
  { kind: "agent_fail", label: "Kill an agent", short: "Failure", icon: XOctagon, target: "agent", hint: "Hardware failure — the agent is lost and its tasks are re-auctioned." },
  { kind: "battery_drain", label: "Drain a battery", short: "Battery", icon: BatteryLow, target: "agent", hint: "Cell fault: −45% of capacity instantly." },
  { kind: "bridge_collapse", label: "Collapse a bridge", short: "Bridge", icon: Construction, target: "bridge", hint: "Ground routes recompute; deliveries are re-auctioned." },
  { kind: "storm", label: "Storm cell", short: "Storm", icon: CloudLightning, target: "place", radius: 5.5, hint: "Click the map to place a 70-tick storm. Drones inside fly at half speed and risk loss." },
  { kind: "comm_blackout", label: "Comm blackout", short: "Blackout", icon: WifiOff, target: "place", radius: 4, hint: "Click the map to place a dead zone. Agents inside lose their link." },
  { kind: "new_target", label: "Emergency call", short: "New survivor", icon: PhoneCall, target: "place", radius: 0.8, hint: "Click the map where the caller is. A delivery task is created immediately." },
];

export const CONNECTION_ICON = Radio;

export const pct = (p: number | null | undefined, digits = 0) =>
  p == null || Number.isNaN(p) ? "—" : `${(p * 100).toFixed(digits)}%`;

export const fmt = (v: number | null | undefined, digits = 1) =>
  v == null || Number.isNaN(v) ? "—" : v.toFixed(digits);

export function forecastStatus(p: number, threshold: number) {
  if (p >= 0.8) return { tone: "good", label: "On track" } as const;
  if (p >= threshold) return { tone: "warning", label: "At risk" } as const;
  return { tone: "critical", label: "Below threshold" } as const;
}

export function batteryTone(b: number) {
  return b > 0.45 ? "good" : b > 0.25 ? "warning" : "critical";
}

export function cleanLogText(text: string) {
  const t = text
    .replace(/^EVENT:\s*/, "")
    .replace(/^ESCALATION:\s*/, "")
    .replace(/->/g, "→")
    .replace(/\(VoI priority\)/, "(value-of-information priority)")
    .replace(/\s+-\s+/g, " — ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

export function splitDetail(text: string): [string, string | null] {
  const i = text.indexOf(" (");
  // "(36, 23)" is a map cell, not a detail — keep it inline
  if (i > 0 && text.endsWith(")") && !/^\d+, \d+$/.test(text.slice(i + 2, -1))) return [text.slice(0, i), text.slice(i + 2, -1)];
  return [text, null];
}

export const TICK_SECONDS = 10;
export const ticksToClock = (t: number) => {
  const s = t * TICK_SECONDS;
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
};
