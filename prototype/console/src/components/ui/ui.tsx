import { X } from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import "./ui.css";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "warning";

export function Button({
  variant = "secondary",
  size = "md",
  icon,
  iconRight,
  className = "",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  iconRight?: ReactNode;
}) {
  return (
    <button className={`btn btn-${variant} btn-${size} ${className}`} {...rest}>
      {icon}
      {children && <span>{children}</span>}
      {iconRight}
    </button>
  );
}

export function IconButton({
  label,
  className = "",
  active,
  children,
  tooltip = true,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; active?: boolean; tooltip?: boolean }) {
  const btn = (
    <button aria-label={label} className={`icon-btn ${active ? "is-active" : ""} ${className}`} {...rest}>
      {children}
    </button>
  );
  return tooltip ? <Tooltip content={label}>{btn}</Tooltip> : btn;
}

export function Badge({
  tone = "neutral",
  children,
  icon,
  dot,
  className = "",
}: {
  tone?: "neutral" | "accent" | "good" | "warning" | "serious" | "critical";
  children: ReactNode;
  icon?: ReactNode;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span className={`badge badge-${tone} ${className}`}>
      {dot && <span className="badge-dot" />}
      {icon}
      {children}
    </span>
  );
}

export function Tooltip({
  content,
  children,
  side = "top",
  className = "",
}: {
  content: ReactNode;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}) {
  return (
    <span className={`tt ${className}`}>
      {children}
      <span role="tooltip" className={`tt-bubble tt-${side}`}>
        {content}
      </span>
    </span>
  );
}

export function Meter({
  value,
  tone = "accent",
  label,
  height = 6,
}: {
  value: number;
  tone?: string;
  label?: string;
  height?: number;
}) {
  const v = Math.max(0, Math.min(1, value));
  return (
    <div
      className="meter"
      style={{ height }}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(v * 100)}
      aria-label={label}
    >
      <div className={`meter-fill tone-${tone}`} style={{ width: `${v * 100}%` }} />
    </div>
  );
}

export function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  size = "md",
  label,
}: {
  value: T;
  options: { value: T; label: ReactNode; title?: string }[];
  onChange: (v: T) => void;
  size?: "sm" | "md";
  label: string;
}) {
  return (
    <div className={`segmented seg-${size}`} role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button
          key={String(o.value)}
          role="radio"
          aria-checked={o.value === value}
          title={o.title}
          className={o.value === value ? "is-active" : ""}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function useDismiss(open: boolean, onClose: () => void, ref: React.RefObject<HTMLElement>) {
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    const click = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", key);
    window.addEventListener("mousedown", click);
    return () => {
      window.removeEventListener("keydown", key);
      window.removeEventListener("mousedown", click);
    };
  }, [open, onClose, ref]);
}

export function Popover({
  trigger,
  children,
  align = "start",
  side = "top",
  open: openProp,
  onOpenChange,
}: {
  trigger: (props: { open: boolean; toggle: () => void }) => ReactNode;
  children: (close: () => void) => ReactNode;
  align?: "start" | "center" | "end";
  side?: "top" | "bottom";
  open?: boolean;
  onOpenChange?: (o: boolean) => void;
}) {
  const [inner, setInner] = useState(false);
  const open = openProp ?? inner;
  const set = (o: boolean) => (onOpenChange ? onOpenChange(o) : setInner(o));
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(open, () => set(false), ref);
  return (
    <div className="popover-anchor" ref={ref}>
      {trigger({ open, toggle: () => set(!open) })}
      {open && <div className={`popover pop-${side} pop-${align}`}>{children(() => set(false))}</div>}
    </div>
  );
}

export function Drawer({
  open,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [open, onClose]);
  if (!open) return null;
  return createPortal(
    <div className="drawer-layer">
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={typeof title === "string" ? title : undefined}>
        <header className="drawer-head">
          {icon && <div className="drawer-icon">{icon}</div>}
          <div className="drawer-titles">
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <IconButton label="Close" onClick={onClose} tooltip={false}>
            <X size={16} />
          </IconButton>
        </header>
        <div className="drawer-body">{children}</div>
        {footer && <footer className="drawer-foot">{footer}</footer>}
      </aside>
    </div>,
    document.body,
  );
}

export function Modal({
  open,
  onClose,
  children,
  width = 640,
  label,
  dismissable = true,
  className = "",
}: {
  open: boolean;
  onClose?: () => void;
  children: ReactNode;
  width?: number;
  label: string;
  dismissable?: boolean;
  className?: string;
}) {
  useEffect(() => {
    if (!open || !dismissable) return;
    const key = (e: KeyboardEvent) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [open, onClose, dismissable]);
  if (!open) return null;
  return createPortal(
    <div className="modal-layer">
      <div className="modal-scrim" onClick={dismissable ? onClose : undefined} />
      <div
        className={`modal ${className}`}
        role="dialog"
        aria-modal="true"
        aria-label={label}
        style={{ "--modal-w": `${width}px` } as CSSProperties}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}

export function SectionHeader({
  title,
  icon,
  actions,
  info,
}: {
  title: string;
  icon?: ReactNode;
  actions?: ReactNode;
  info?: ReactNode;
}) {
  return (
    <div className="section-head">
      <div className="section-title">
        {icon}
        <h3>{title}</h3>
        {info && (
          <Tooltip content={info} side="bottom" className="tt-wide">
            <span className="info-dot" tabIndex={0} aria-label="More information">
              ?
            </span>
          </Tooltip>
        )}
      </div>
      {actions && <div className="section-actions">{actions}</div>}
    </div>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="kbd">{children}</kbd>;
}

export function Spinner({ size = 14 }: { size?: number }) {
  return <span className="spinner" style={{ width: size, height: size }} aria-hidden />;
}

export function EmptyState({ icon, title, body }: { icon: ReactNode; title: string; body?: ReactNode }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <p className="empty-title">{title}</p>
      {body && <p className="empty-body">{body}</p>}
    </div>
  );
}
