import { ChevronRight, ScrollText } from "lucide-react";
import { useMemo, useState } from "react";
import { cleanLogText, LOG_FILTERS, LOG_META, splitDetail, type LogCategory } from "../../lib/meta";
import type { LogEntry } from "../../lib/types";
import { EmptyState, SectionHeader } from "../ui/ui";
import "./log.css";

interface Props {
  log: LogEntry[];
  onFocus: (e: LogEntry) => void;
}

export function DecisionLog({ log, onFocus }: Props) {
  const [filter, setFilter] = useState<LogCategory | "all">("all");
  const [open, setOpen] = useState<Set<number>>(new Set());

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: log.length };
    log.forEach((e) => {
      const cat = LOG_META[e.kind]?.category ?? "allocation";
      c[cat] = (c[cat] ?? 0) + 1;
    });
    return c;
  }, [log]);

  const items = useMemo(
    () => [...log].reverse().filter((e) => filter === "all" || LOG_META[e.kind]?.category === filter),
    [log, filter],
  );

  const toggle = (i: number) =>
    setOpen((s) => {
      const n = new Set(s);
      n.has(i) ? n.delete(i) : n.add(i);
      return n;
    });

  return (
    <section className="panel log-panel" aria-label="Decision log">
      <SectionHeader
        title="Decision log"
        icon={<ScrollText />}
        info="Every autonomous decision with a one-line reason, written by the engine as it decides. Re-plans expand to show the auction: winning bid and every other agent's bid."
        actions={<span className="subtle num log-count">{log.length} entries</span>}
      />
      <div className="log-filters" role="tablist" aria-label="Filter decision log">
        {LOG_FILTERS.map((f) => (
          <button
            key={f.id}
            role="tab"
            aria-selected={filter === f.id}
            className={`chip ${filter === f.id ? "is-active" : ""}`}
            onClick={() => setFilter(f.id)}
            disabled={f.id !== "all" && !counts[f.id]}
          >
            {f.label}
            {counts[f.id] ? <span className="chip-count num">{counts[f.id]}</span> : null}
          </button>
        ))}
      </div>
      <ol className="log-list">
        {items.length === 0 && (
          <EmptyState icon={<ScrollText size={16} />} title="Nothing logged yet" body="Decisions appear here as the swarm plans and re-plans." />
        )}
        {items.map((e) => {
          const meta = LOG_META[e.kind] ?? LOG_META.assign;
          const Icon = meta.icon;
          const [main, detail] = splitDetail(cleanLogText(e.text));
          const expandable = !!(e.bids && e.bids.length);
          const isOpen = open.has(e.i);
          const focusable = !!(e.agent || e.sid);
          return (
            <li key={e.i} className={`log-item tone-${meta.tone}`}>
              <span className="log-time num">t={e.t}</span>
              <span className="log-icon" title={meta.label}>
                <Icon />
              </span>
              <div className="log-body">
                <button
                  className={`log-text ${focusable || expandable ? "is-interactive" : ""}`}
                  onClick={() => (expandable ? toggle(e.i) : focusable && onFocus(e))}
                  aria-expanded={expandable ? isOpen : undefined}
                >
                  <span>{main}</span>
                  {expandable && <ChevronRight className={`log-chevron ${isOpen ? "is-open" : ""}`} />}
                </button>
                {detail && <div className="log-detail">{detail}</div>}
                {e.released && e.released.length > 0 && (
                  <div className="log-detail">Released: {e.released.join(", ")}</div>
                )}
                {expandable && isOpen && <BidTable entry={e} />}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function BidTable({ entry }: { entry: LogEntry }) {
  return (
    <div className="bid-table-wrap">
      <table className="bid-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Winner</th>
            <th className="r">Bid</th>
            <th className="r">ETA</th>
            <th>Other bids</th>
          </tr>
        </thead>
        <tbody>
          {entry.bids!.map((b) => (
            <tr key={b.task}>
              <td>{b.label}</td>
              <td>
                {b.winner}
                {b.via_base && <span className="subtle"> · via base</span>}
              </td>
              <td className="r num">{b.bid.toFixed(2)}</td>
              <td className="r num">t+{Math.round(b.eta)}</td>
              <td className="bid-others">
                {b.others.map((o) => (
                  <span key={o.agent} className={o.bid == null ? "subtle" : ""}>
                    {o.agent} {o.bid == null ? "—" : o.bid.toFixed(2)}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="bid-note">
        Bid = priority · e<sup>−t/τ</sup> − β·energy − γ·risk (+δ to keep the current owner). “—” = ineligible (capability, battery reserve or risk ceiling).
      </p>
    </div>
  );
}
