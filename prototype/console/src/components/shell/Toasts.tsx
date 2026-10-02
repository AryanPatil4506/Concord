import { CircleAlert, CircleCheck, Info, TriangleAlert, X } from "lucide-react";
import { useEffect } from "react";
import type { Notice } from "../../lib/mission";

const ICON = { warning: TriangleAlert, error: CircleAlert, info: Info, success: CircleCheck };

function Toast({ n, onDismiss }: { n: Notice; onDismiss: (id: number) => void }) {
  useEffect(() => {
    const id = window.setTimeout(() => onDismiss(n.id), 4500);
    return () => window.clearTimeout(id);
  }, [n.id, onDismiss]);
  const Icon = ICON[n.level];
  return (
    <div className={`toast toast-${n.level}`} role="status">
      <Icon size={16} />
      <span>{n.message}</span>
      <button aria-label="Dismiss" onClick={() => onDismiss(n.id)}>
        <X size={14} />
      </button>
    </div>
  );
}

export function Toasts({ notices, onDismiss }: { notices: Notice[]; onDismiss: (id: number) => void }) {
  return (
    <div className="toasts" aria-live="polite">
      {notices.map((n) => (
        <Toast key={n.id} n={n} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
