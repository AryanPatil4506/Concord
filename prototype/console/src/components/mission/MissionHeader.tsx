import { FileText, Pause, Play, StepForward } from "lucide-react";
import { ticksToClock } from "../../lib/meta";
import type { MissionSnapshot, Phase } from "../../lib/types";
import { Badge, IconButton, Popover, Segmented, Spinner } from "../ui/ui";
import "./header.css";

const PHASE: Record<Phase, { label: string; tone: "good" | "neutral" | "accent" | "warning" }> = {
  running: { label: "Live", tone: "good" },
  paused: { label: "Paused", tone: "neutral" },
  assessing: { label: "Re-forecasting", tone: "accent" },
  escalation: { label: "Awaiting decision", tone: "warning" },
  complete: { label: "Complete", tone: "neutral" },
};

const SPEEDS = [0.5, 1, 2, 4];

export function MissionHeader({
  mission,
  onPlay,
  onPause,
  onStep,
  onSpeed,
}: {
  mission: MissionSnapshot;
  onPlay: () => void;
  onPause: () => void;
  onStep: () => void;
  onSpeed: (m: number) => void;
}) {
  const { state, static: st, phase } = mission;
  const ph = PHASE[phase];
  const progress = Math.min(1, state.t / st.tmax);
  const mult = Math.round((mission.tps / mission.base_tps) * 100) / 100;
  const canPlay = phase === "paused";
  const canPause = phase === "running";

  return (
    <div className="mhead">
      <div className="mhead-title">
        <div className="mhead-name">
          <h1>{mission.scenario_title}</h1>
          <Badge tone="neutral" className="num">
            seed {st.seed}
          </Badge>
          <Popover
            side="bottom"
            align="start"
            trigger={({ toggle, open }) => (
              <IconButton label="Mission objective" onClick={toggle} active={open}>
                <FileText size={15} />
              </IconButton>
            )}
          >
            {() => (
              <div className="objective-pop">
                <div className="eyebrow">Operator objective</div>
                <p>{mission.objective || "Default flood-response objective"}</p>
                <div className="subtle">
                  {mission.scheduled > 0
                    ? `${mission.scheduled} disruptions scheduled by the scenario — revealed only when they happen.`
                    : "No scheduled disruptions."}
                </div>
              </div>
            )}
          </Popover>
        </div>
        <p className="mhead-sub">Simulated 2 × 1.4 km flood zone · 1 tick ≈ 10 s</p>
      </div>

      <div className="mhead-clock" aria-label={`Mission time t=${state.t} of ${st.tmax}`}>
        <div className="clock-row">
          <span className="clock-t num">
            t={String(state.t).padStart(3, "0")}
          </span>
          <span className="subtle num">/ {st.tmax}</span>
          <span className="clock-real subtle num">≈ {ticksToClock(state.t)} min</span>
        </div>
        <div className="clock-track">
          <div className="clock-fill" style={{ width: `${progress * 100}%` }} />
        </div>
      </div>

      <div className="mhead-controls">
        <Badge tone={ph.tone} dot={phase === "running"} icon={phase === "assessing" ? <Spinner size={10} /> : undefined} className={`phase-badge phase-${phase}`}>
          {ph.label}
        </Badge>
        <div className="playback">
          {canPause ? (
            <IconButton label="Pause (Space)" onClick={onPause}>
              <Pause size={16} />
            </IconButton>
          ) : (
            <IconButton label="Play (Space)" onClick={onPlay} disabled={!canPlay}>
              <Play size={16} />
            </IconButton>
          )}
          <IconButton label="Step one tick (→)" onClick={onStep} disabled={phase !== "paused"}>
            <StepForward size={16} />
          </IconButton>
        </div>
        <Segmented
          label="Simulation speed"
          size="sm"
          value={mult}
          options={SPEEDS.map((s) => ({ value: s, label: `${s}×`, title: `${s * mission.base_tps} ticks per second` }))}
          onChange={onSpeed}
        />
      </div>
    </div>
  );
}
