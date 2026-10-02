import { ArrowRight, Check, CircleAlert, Cpu, Rocket, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useMission } from "../../lib/mission";
import type { CompiledMission, ScenarioInfo } from "../../lib/types";
import { AgentGlyph } from "../glyphs";
import { Badge, Button, EmptyState, Spinner } from "../ui/ui";
import { TaskGraph } from "./TaskGraph";
import "./briefing.css";

const FLEET_PREVIEW = [
  { id: "Scout-1", kind: "scout" as const },
  { id: "Scout-2", kind: "scout" as const },
  { id: "Cargo-1", kind: "cargo" as const },
  { id: "Rover-1", kind: "rover" as const },
  { id: "Relay-1", kind: "relay" as const },
];

const sentence = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

export function Briefing() {
  const { store, actions } = useMission();
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [scenario, setScenario] = useState("storyboard");
  const [seed, setSeed] = useState("");
  const [objective, setObjective] = useState("");
  const [compiled, setCompiled] = useState<CompiledMission | null>(null);
  const [busy, setBusy] = useState<"compile" | "deploy" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetch("/api/scenarios").then((r) => r.json()), fetch("/api/default-objective").then((r) => r.json())])
      .then(([sc, obj]) => {
        setScenarios(sc);
        setObjective((o) => o || obj.text);
      })
      .catch(() => setError("Can't reach the engine. Start it with `python -m server`."));
  }, [store.connection]);

  const current = scenarios.find((s) => s.id === scenario);
  const step = compiled ? 2 : 1;

  const compile = async () => {
    setBusy("compile");
    setError(null);
    try {
      const r = await fetch("/api/compile", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: objective, scenario }),
      });
      if (!r.ok) throw new Error();
      const [data] = await Promise.all([r.json(), new Promise((res) => setTimeout(res, 450))]);
      setCompiled(data);
    } catch {
      setError("Compilation failed — is the engine running?");
    } finally {
      setBusy(null);
    }
  };

  const deploy = () => {
    if (!compiled) return;
    setBusy("deploy");
    actions.start({
      scenario,
      seed: current?.fixed_seed == null && seed ? Number(seed) : null,
      objective: compiled.objective,
      sectors: compiled.sectors,
    });
  };

  const allOk = compiled?.checks.every((c) => c.ok);

  return (
    <div className="brief">
      <div className="brief-intro">
        <div className="eyebrow">New mission</div>
        <h1>Tell the swarm what you want done.</h1>
        <p className="muted">
          CONCORD turns your objective into a task graph, auctions the work across a mixed air–ground team, re-plans the moment the world
          changes, and asks you only when the odds drop.
        </p>
        <ol className="brief-steps" aria-label="Progress">
          {["Objective", "Review task graph", "Deploy"].map((s, i) => (
            <li key={s} className={i + 1 < step ? "is-done" : i + 1 === step ? "is-current" : ""}>
              <span className="brief-step-n">{i + 1 < step ? <Check size={12} /> : i + 1}</span>
              {s}
            </li>
          ))}
        </ol>
      </div>

      <div className="brief-grid">
        <section className="brief-card brief-form">
          <label className="field">
            <span className="field-label">Objective</span>
            <textarea
              rows={5}
              value={objective}
              onChange={(e) => {
                setObjective(e.target.value);
                setCompiled(null);
              }}
              placeholder="Describe the mission in plain English…"
            />
            <span className="field-hint">Mention sectors (A–D), med-kit delivery, comms, or a deadline (“within 180 ticks”).</span>
          </label>

          <fieldset className="field">
            <legend className="field-label">Scenario</legend>
            <div className="scenario-list" role="radiogroup">
              {scenarios.length === 0 &&
                [0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 62 }} />)}
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  role="radio"
                  aria-checked={scenario === s.id}
                  className={`scenario ${scenario === s.id ? "is-selected" : ""}`}
                  onClick={() => {
                    setScenario(s.id);
                    setCompiled(null);
                  }}
                >
                  <span className="scenario-radio" />
                  <span>
                    <span className="scenario-title">
                      {sentence(s.title.replace("Flood SAR · ", ""))}
                      {s.id === "storyboard" && <Badge tone="accent">Demo</Badge>}
                    </span>
                    <span className="scenario-blurb">{s.blurb}</span>
                  </span>
                </button>
              ))}
            </div>
          </fieldset>

          {current && current.fixed_seed == null && (
            <label className="field field-inline">
              <span className="field-label">Seed</span>
              <input
                type="number"
                inputMode="numeric"
                placeholder="Random"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
              />
              <span className="field-hint">Same seed → same map, survivors and disruptions.</span>
            </label>
          )}

          {error && (
            <div className="brief-error" role="alert">
              <CircleAlert size={15} /> {error}
            </div>
          )}

          <Button
            variant={compiled ? "secondary" : "primary"}
            size="lg"
            icon={busy === "compile" ? <Spinner /> : <Wand2 size={16} />}
            onClick={compile}
            disabled={!!busy || store.connection !== "open" || !objective.trim()}
          >
            {compiled ? "Recompile" : busy === "compile" ? "Compiling…" : "Compile mission"}
          </Button>
        </section>

        <section className="brief-card brief-plan" aria-live="polite">
          {!compiled ? (
            <div className="brief-placeholder">
              {busy === "compile" ? (
                <div className="brief-compiling">
                  <Spinner size={20} />
                  <p>Parsing objective · building task graph · validating against map and fleet…</p>
                </div>
              ) : (
                <EmptyState
                  icon={<Sparkles size={16} />}
                  title="Your task graph appears here"
                  body="Compile the objective to see the tasks, dependencies, constraints and validation checks before anything moves."
                />
              )}
              <blockquote className="brief-principle">
                “LLMs understand intent. Algorithms make decisions. Humans own the hard calls.”
              </blockquote>
              <div className="brief-fleet">
                <div className="eyebrow">Fleet</div>
                <div className="brief-fleet-row">
                  {FLEET_PREVIEW.map((a) => (
                    <span key={a.id} className="brief-agent">
                      <AgentGlyph kind={a.kind} /> {a.id}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="brief-result">
              <div className="brief-result-head">
                <div>
                  <h2>Mission task graph</h2>
                  <p className="subtle">
                    {compiled.task_count} survey waypoints in sector{compiled.sectors.length > 1 ? "s" : ""} {compiled.sectors.join(", ")} ·
                    delivery tasks spawn as survivors are reported
                  </p>
                </div>
                <Badge icon={<Cpu />} tone="neutral">
                  {compiled.compiler}
                </Badge>
              </div>

              <div className="tg-scroll">
                <TaskGraph mission={compiled} />
              </div>

              <div className="brief-two">
                <div>
                  <div className="eyebrow">Constraints</div>
                  <dl className="brief-dl">
                    {compiled.constraints.map((c) => (
                      <div key={c.label}>
                        <dt>{c.label}</dt>
                        <dd>{c.value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <div>
                  <div className="eyebrow">Validation</div>
                  <ul className="brief-checks">
                    {compiled.checks.map((c) => (
                      <li key={c.label} className={c.ok ? "ok" : "bad"}>
                        {c.ok ? <Check size={14} /> : <CircleAlert size={14} />}
                        {c.label}
                      </li>
                    ))}
                  </ul>
                  <div className="eyebrow" style={{ marginTop: 16 }}>
                    Capable agents
                  </div>
                  <dl className="brief-dl">
                    {Object.entries(compiled.capabilities).map(([cap, ids]) => (
                      <div key={cap}>
                        <dt>{cap}</dt>
                        <dd>{ids.join(", ")}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>

              <div className="brief-deploy">
                <p className="subtle">
                  The offline compiler fills the same typed schema an LLM compiler would, then the map and fleet checks run. Nothing here is
                  model-generated. Confirming hands the graph to the auction.
                </p>
                <Button
                  variant="primary"
                  size="lg"
                  icon={busy === "deploy" ? <Spinner /> : <Rocket size={16} />}
                  iconRight={busy ? undefined : <ArrowRight size={16} />}
                  disabled={!allOk || !!busy || store.connection !== "open"}
                  onClick={deploy}
                >
                  Confirm &amp; deploy
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
