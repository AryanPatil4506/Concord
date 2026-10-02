import { AGENT_META } from "../lib/meta";
import type { AgentKind } from "../lib/types";

export function agentPath(kind: AgentKind, r: number) {
  switch (kind) {
    case "scout":
      return `M0 ${-r * 1.1} L${r} ${r * 0.75} L${-r} ${r * 0.75} Z`;
    case "cargo":
      return `M0 ${r * 1.1} L${r} ${-r * 0.75} L${-r} ${-r * 0.75} Z`;
    case "rover": {
      const s = r * 0.82;
      return `M${-s} ${-s} H${s} V${s} H${-s} Z`;
    }
    case "relay":
      return `M0 ${-r * 1.12} L${r * 1.0} 0 L0 ${r * 1.12} L${-r * 1.0} 0 Z`;
  }
}

export function AgentGlyph({
  kind,
  size = 14,
  lost = false,
  title,
}: {
  kind: AgentKind;
  size?: number;
  lost?: boolean;
  title?: string;
}) {
  return (
    <svg width={size} height={size} viewBox="-12 -12 24 24" aria-hidden={!title} role={title ? "img" : undefined}>
      {title && <title>{title}</title>}
      <path
        d={agentPath(kind, 9)}
        fill={lost ? "var(--agent-lost)" : AGENT_META[kind].color}
        stroke="rgba(0,0,0,0.35)"
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
    </svg>
  );
}

export type SurvivorStatus = "hidden" | "detected" | "reported" | "delivered";

export const SURVIVOR_META: Record<SurvivorStatus, { label: string; color: string; description: string }> = {
  hidden: { label: "Not yet found", color: "var(--text-3)", description: "Ground truth — unknown to the swarm" },
  detected: { label: "Found · report pending", color: "var(--warning)", description: "Seen by a scout; base not yet informed" },
  reported: { label: "Awaiting aid", color: "var(--critical)", description: "Base knows; delivery task auctioned" },
  delivered: { label: "Aid delivered", color: "var(--good)", description: "Med-kit delivered" },
};

export function SurvivorMark({ status, r = 0.62 }: { status: SurvivorStatus; r?: number }) {
  const c = SURVIVOR_META[status].color;
  if (status === "delivered") {
    return (
      <g>
        <circle r={r} fill={c} stroke="var(--bg)" strokeWidth={0.14} />
        <path
          d={`M${-r * 0.45} 0 L${-r * 0.1} ${r * 0.35} L${r * 0.5} ${-r * 0.35}`}
          fill="none"
          stroke="#fff"
          strokeWidth={0.17}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    );
  }
  const a = r * 0.36;
  const b = r;
  const plus = `M${-a} ${-b} H${a} V${-a} H${b} V${a} H${a} V${b} H${-a} V${a} H${-b} V${-a} H${-a} Z`;
  if (status === "hidden") {
    return <path d={plus} fill="none" stroke={c} strokeWidth={0.1} strokeDasharray="0.2 0.15" />;
  }
  return <path d={plus} fill={c} stroke="var(--bg)" strokeWidth={0.14} strokeLinejoin="round" />;
}

export function SurvivorGlyph({ status, size = 14 }: { status: SurvivorStatus; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="-0.8 -0.8 1.6 1.6" aria-hidden>
      <SurvivorMark status={status} r={0.7} />
    </svg>
  );
}

export function survivorStatus(s: { detected_t: number | null; reported_t: number | null; delivered_t: number | null }): SurvivorStatus {
  if (s.delivered_t != null) return "delivered";
  if (s.reported_t != null) return "reported";
  if (s.detected_t != null) return "detected";
  return "hidden";
}

export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="8" fill="var(--accent)" />
      <path d="M16 7.5l8 13.5H8z" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinejoin="round" />
      <circle cx="16" cy="16.6" r="2.4" fill="#fff" />
    </svg>
  );
}
