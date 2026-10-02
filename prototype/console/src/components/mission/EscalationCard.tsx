import { AlertTriangle, Check, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { useNow } from "../../lib/hooks";
import { forecastStatus, pct } from "../../lib/meta";
import type { Escalation } from "../../lib/types";
import { Badge, Button, Kbd, Meter } from "../ui/ui";
import "./escalation.css";

export function EscalationCard({
  escalation,
  receivedAt,
  threshold,
  onDecide,
}: {
  escalation: Escalation;
  receivedAt: number;
  threshold: number;
  onDecide: (key: string) => void;
}) {
  const [choice, setChoice] = useState(escalation.recommend);
  const [sent, setSent] = useState(false);
  const now = useNow(true, 200);
  const remaining = Math.max(0, escalation.remaining_s - (now - receivedAt) / 1000);
  const frac = remaining / escalation.timeout_s;

  useEffect(() => {
    setChoice(escalation.recommend);
    setSent(false);
  }, [escalation.id, escalation.recommend]);

  const approve = () => {
    if (sent) return;
    setSent(true);
    onDecide(choice);
  };

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT" || (e.target as HTMLElement)?.tagName === "TEXTAREA") return;
      const k = e.key.toUpperCase();
      const byLetter = escalation.options.find((o) => o.key === k);
      const byNum = escalation.options[Number(e.key) - 1];
      if (byLetter || byNum) setChoice((byLetter ?? byNum)!.key);
      if (e.key === "Enter") approve();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  });

  const C = 2 * Math.PI * 15;

  return (
    <div className="esc-layer" role="alertdialog" aria-modal="false" aria-labelledby="esc-title" aria-describedby="esc-situation">
      <div className="esc-card">
        <header className="esc-head">
          <div className="esc-icon">
            <AlertTriangle />
          </div>
          <div className="esc-titles">
            <div className="eyebrow esc-eyebrow">Escalation · t={escalation.t}</div>
            <h2 id="esc-title">Operator decision needed</h2>
          </div>
          <div className="esc-timer" title="A safe default executes when the timer runs out">
            <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden>
              <circle cx="20" cy="20" r="15" className="esc-timer-track" />
              <circle
                cx="20"
                cy="20"
                r="15"
                className="esc-timer-fill"
                strokeDasharray={C}
                strokeDashoffset={C * (1 - frac)}
              />
            </svg>
            <span className="num">{Math.ceil(remaining)}s</span>
          </div>
        </header>

        <p id="esc-situation" className="esc-situation">
          {escalation.situation}
        </p>

        <div className="esc-forecast">
          <span className="subtle">Current plan</span>
          <Badge tone={forecastStatus(escalation.p_now, threshold).tone}>P(success) {pct(escalation.p_now)}</Badge>
          <span className="subtle">· threshold {pct(threshold)}</span>
        </div>

        <div className="esc-options" role="radiogroup" aria-label="Options">
          {escalation.options.map((o, i) => {
            const rec = o.key === escalation.recommend;
            const st = forecastStatus(o.p, threshold);
            return (
              <button
                key={o.key}
                role="radio"
                aria-checked={choice === o.key}
                className={`esc-option ${choice === o.key ? "is-selected" : ""}`}
                onClick={() => setChoice(o.key)}
              >
                <span className="esc-key">{o.key}</span>
                <span className="esc-opt-main">
                  <span className="esc-opt-title">
                    {o.title}
                    {rec && (
                      <Badge tone="accent" icon={<Check />}>
                        Recommended
                      </Badge>
                    )}
                    {o.irreversible && (
                      <Badge tone="serious" icon={<ShieldAlert />}>
                        Irreversible risk
                      </Badge>
                    )}
                  </span>
                  <span className="esc-opt-detail">{o.detail}</span>
                </span>
                <span className="esc-opt-p">
                  <span className={`num esc-p tone-text-${st.tone}`}>{pct(o.p)}</span>
                  <Meter value={o.p} tone={st.tone} height={4} label={`Option ${o.key} success probability`} />
                </span>
                <Kbd>{i + 1}</Kbd>
              </button>
            );
          })}
        </div>

        <footer className="esc-foot">
          <p className="subtle">
            Each option scored by {escalation.k} rollouts. If nobody answers, option {escalation.recommend} runs as the safe default.
          </p>
          <Button variant="warning" size="lg" onClick={approve} disabled={sent} iconRight={<Kbd>↵</Kbd>}>
            Approve option {choice}
          </Button>
        </footer>
      </div>
    </div>
  );
}
