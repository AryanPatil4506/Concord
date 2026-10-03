import { CircleCheckBig, Crosshair, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { DEMO } from "../../lib/api";
import { useMission } from "../../lib/mission";
import { DISRUPTIONS } from "../../lib/meta";
import type { DisruptionKind, LogEntry, MissionSnapshot } from "../../lib/types";
import { MissionMap, type MapLayers, type Placement, type Selection } from "../map/MissionMap";
import { Spinner } from "../ui/ui";
import { DecisionLog } from "./DecisionLog";
import { DetailDrawer } from "./DetailDrawer";
import { DisruptionDock } from "./DisruptionDock";
import { EscalationCard } from "./EscalationCard";
import { ForecastPanel } from "./ForecastPanel";
import { KpiStrip } from "./KpiStrip";
import { LayerMenu, Legend } from "./MapControls";
import { MissionHeader } from "./MissionHeader";
import { MissionSummary } from "./MissionSummary";
import { SwarmPanel } from "./SwarmPanel";
import "./mission.css";

const DEFAULT_LAYERS: MapLayers = { links: true, routes: true, surveys: true, labels: true, truth: false, ranges: false };

const PLACE_COLOR: Partial<Record<DisruptionKind, string>> = {
  storm: "var(--map-storm)",
  comm_blackout: "var(--critical)",
  new_target: "var(--warning)",
};

export function MissionView({ mission, onNewMission }: { mission: MissionSnapshot; onNewMission: () => void }) {
  const { store, actions } = useMission();
  const [layers, setLayers] = useState<MapLayers>(() => {
    try {
      return { ...DEFAULT_LAYERS, ...JSON.parse(localStorage.getItem("concord.layers") ?? "{}") };
    } catch {
      return DEFAULT_LAYERS;
    }
  });
  const [selection, setSelection] = useState<Selection>(null);
  const [placing, setPlacing] = useState<DisruptionKind | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem("concord.layers", JSON.stringify(layers));
    } catch {
      /* storage unavailable */
    }
  }, [layers]);

  useEffect(() => {
    if (mission.summary) setSummaryOpen(true);
  }, [mission.summary]);

  const { phase } = mission;
  const injectBlocked =
    phase === "assessing"
      ? "Wait for the re-forecast to finish"
      : phase === "escalation"
        ? "Answer the escalation first"
        : phase === "complete"
          ? "The mission is complete"
          : DEMO
            ? "Live injection needs the engine running locally — this hosted demo replays recorded missions. Try the “Operator chaos” mission to watch injected disruptions."
            : null;

  useEffect(() => {
    if (injectBlocked) setPlacing(null);
  }, [injectBlocked]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement)?.isContentEditable) return;
      if (e.key === " " && (tag !== "BUTTON" || !(e.target as HTMLElement).closest(".dock, .esc-layer"))) {
        e.preventDefault();
        phase === "running" ? actions.pause() : phase === "paused" && actions.play();
      } else if (e.key === "ArrowRight" && phase === "paused") {
        actions.step();
      } else if (e.key === "Escape") {
        setPlacing(null);
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [phase, actions]);

  const placement: Placement | null = useMemo(() => {
    if (!placing) return null;
    const d = DISRUPTIONS.find((x) => x.kind === placing)!;
    return { label: d.label, radius: d.radius ?? 1, color: PLACE_COLOR[placing] ?? "var(--warning)" };
  }, [placing]);

  const onPlace = useCallback(
    (pos: [number, number]) => {
      if (!placing) return;
      actions.inject(placing, { pos });
      setPlacing(null);
    },
    [placing, actions],
  );

  const onFocus = useCallback((e: LogEntry) => {
    if (e.agent) setSelection({ type: "agent", id: e.agent });
    else if (e.sid) setSelection({ type: "survivor", id: e.sid });
  }, []);

  const placingMeta = placing ? DISRUPTIONS.find((d) => d.kind === placing) : null;
  const tickSeconds = 1 / mission.tps;

  return (
    <div className="mission">
      <div className="mission-main">
        <MissionHeader
          mission={mission}
          onPlay={actions.play}
          onPause={actions.pause}
          onStep={actions.step}
          onSpeed={actions.speed}
        />
        <KpiStrip m={mission.state.metrics} />

        <div className={`map-card ${phase === "escalation" ? "is-escalated" : ""}`}>
          <MissionMap
            mission={mission}
            layers={layers}
            selection={selection}
            onSelect={setSelection}
            placement={placement}
            onPlace={onPlace}
            tickSeconds={phase === "running" ? tickSeconds : 0.2}
          />

          <div className="map-overlay-top">
            <div className="map-banners">
              {store.assessing && (
                <div className="banner banner-accent" role="status">
                  <Spinner size={12} />
                  <span>
                    <strong>{store.assessing}</strong> · scoring the current plan with 40 Monte-Carlo rollouts
                  </span>
                </div>
              )}
              {placingMeta && (
                <div className="banner banner-warning" role="status">
                  <Crosshair size={14} />
                  <span>{placingMeta.hint}</span>
                  <button className="banner-btn" onClick={() => actions.inject(placingMeta.kind)} title="Let the engine pick a seeded random location">
                    Random spot
                  </button>
                  <button className="banner-x" aria-label="Cancel placement (Esc)" onClick={() => setPlacing(null)}>
                    <X size={14} />
                  </button>
                </div>
              )}
              {phase === "complete" && !summaryOpen && (
                <div className="banner banner-good" role="status">
                  <CircleCheckBig size={14} />
                  <span>Mission complete</span>
                  <button className="banner-btn" onClick={() => setSummaryOpen(true)}>
                    Open summary
                  </button>
                </div>
              )}
            </div>
            <div className="map-ctls">
              <LayerMenu layers={layers} onChange={setLayers} />
              <Legend />
            </div>
          </div>

          <div className="map-overlay-bottom">
            <DisruptionDock
              agents={mission.state.agents}
              bridges={mission.bridges}
              stormActive={!!mission.state.storm}
              disabledReason={injectBlocked}
              lastInjectAt={store.lastInjectAt}
              cooldownS={mission.cooldown_s}
              placing={placing}
              onPlace={setPlacing}
              onInject={actions.inject}
            />
          </div>

          {phase === "escalation" && mission.escalation && (
            <EscalationCard
              escalation={mission.escalation}
              receivedAt={store.escalationReceivedAt}
              threshold={mission.escalate_below}
              onDecide={actions.decide}
            />
          )}
        </div>
      </div>

      <aside className="mission-rail" aria-label="Mission intelligence">
        <ForecastPanel
          timeline={mission.timeline}
          t={mission.state.t}
          tmax={mission.static.tmax}
          threshold={mission.escalate_below}
          assessing={store.assessing}
        />
        <SwarmPanel
          agents={mission.state.agents}
          selected={selection?.type === "agent" ? selection.id : null}
          onSelect={(id) => setSelection({ type: "agent", id })}
        />
        <DecisionLog log={mission.log} onFocus={onFocus} />
      </aside>

      <DetailDrawer
        mission={mission}
        selection={selection}
        onClose={() => setSelection(null)}
        onInject={actions.inject}
        injectBlocked={injectBlocked}
      />
      <MissionSummary mission={mission} open={summaryOpen} onClose={() => setSummaryOpen(false)} onNew={onNewMission} />
      {phase === "complete" && !summaryOpen && (
        <div className="sr-only" aria-live="polite">
          Mission complete
        </div>
      )}
    </div>
  );
}
