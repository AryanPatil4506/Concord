import { Plus } from "lucide-react";
import type { Connection } from "../../lib/mission";
import { Logo } from "../glyphs";
import { Button, Tooltip } from "../ui/ui";
import "./shell.css";

export type Route = "console" | "evidence" | "method";

const TABS: { id: Route; label: string }[] = [
  { id: "console", label: "Mission console" },
  { id: "evidence", label: "Evidence" },
  { id: "method", label: "Method" },
];

export function TopBar({
  route,
  onRoute,
  connection,
  hasMission,
  onNewMission,
}: {
  route: Route;
  onRoute: (r: Route) => void;
  connection: Connection;
  hasMission: boolean;
  onNewMission: () => void;
}) {
  const conn = {
    open: { label: "Engine live", cls: "is-open", tip: "Connected to the CONCORD v0 engine over WebSocket" },
    connecting: { label: "Connecting…", cls: "is-connecting", tip: "Reaching the engine" },
    closed: { label: "Engine offline", cls: "is-closed", tip: "Reconnecting automatically — is `python -m server` running?" },
  }[connection];

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <Logo />
        <span className="brand-name">CONCORD</span>
        <span className="brand-sub">Swarm mission orchestration</span>
      </div>
      <nav className="topbar-nav" aria-label="Views">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={route === t.id ? "is-active" : ""}
            aria-current={route === t.id ? "page" : undefined}
            onClick={() => onRoute(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="topbar-right">
        <span className="sim-tag">Simulation · v0</span>
        <Tooltip content={conn.tip} side="bottom">
          <span className={`conn ${conn.cls}`} role="status">
            <span className="conn-dot" />
            <span className="conn-label">{conn.label}</span>
          </span>
        </Tooltip>
        {hasMission && (
          <Button variant="secondary" size="sm" icon={<Plus size={14} />} onClick={onNewMission}>
            <span className="hide-sm">New mission</span>
          </Button>
        )}
      </div>
    </header>
  );
}
