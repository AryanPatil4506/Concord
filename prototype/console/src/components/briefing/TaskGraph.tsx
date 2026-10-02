import { Camera, HeartPulse, Package, RadioTower, ScanSearch } from "lucide-react";
import type { ReactNode } from "react";
import { useSize } from "../../lib/hooks";
import type { CompiledMission } from "../../lib/types";

const ICONS: Record<string, ReactNode> = {
  survey: <ScanSearch size={14} />,
  locate: <Camera size={14} />,
  deliver: <Package size={14} />,
  relay: <RadioTower size={14} />,
};

const NODE_H = 54;
const GAP = 10;

export function TaskGraph({ mission }: { mission: CompiledMission }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const surveys = mission.nodes.filter((n) => n.type === "survey");
  const locate = mission.nodes.find((n) => n.type === "locate");
  const deliver = mission.nodes.find((n) => n.type === "deliver");
  const link = mission.nodes.find((n) => n.type === "relay");
  const rows = Math.max(surveys.length, 1);
  const flowH = rows * NODE_H + (rows - 1) * GAP;
  const colW = Math.max(120, (width - 2 * 36) / 3);
  const col = (i: number) => i * (colW + 36);
  const midY = flowH / 2;
  const sy = (i: number) => i * (NODE_H + GAP) + NODE_H / 2;

  const node = (n: (typeof mission.nodes)[number], x: number, y: number, key: string) => (
    <div key={key} className={`tg-node tg-${n.type}`} style={{ left: x, top: y, width: colW, height: NODE_H }}>
      <span className="tg-icon">{ICONS[n.type]}</span>
      <span className="tg-text">
        <span className="tg-label">{n.label}</span>
        <span className="tg-detail">{n.detail}</span>
      </span>
    </div>
  );

  return (
    <div className="tg" ref={ref} style={{ height: flowH + (link ? NODE_H + 28 : 0) }}>
      {width > 0 && (
        <>
          <svg className="tg-edges" width={width} height={flowH} aria-hidden>
            {locate &&
              surveys.map((_, i) => {
                const x1 = col(0) + colW;
                const x2 = col(1);
                const y1 = sy(i);
                const c = (x2 - x1) / 2;
                return <path key={i} d={`M${x1},${y1} C${x1 + c},${y1} ${x2 - c},${midY} ${x2},${midY}`} />;
              })}
            {locate && deliver && <path d={`M${col(1) + colW},${midY} L${col(2)},${midY}`} />}
            {locate && deliver && (
              <path className="tg-arrow" d={`M${col(2) - 6},${midY - 4} L${col(2)},${midY} L${col(2) - 6},${midY + 4}`} />
            )}
          </svg>
          {surveys.map((n, i) => node(n, col(0), i * (NODE_H + GAP), n.id))}
          {locate && node(locate, col(1), midY - NODE_H / 2, locate.id)}
          {deliver && node(deliver, col(2), midY - NODE_H / 2, deliver.id)}
          {link && (
            <div className="tg-lane" style={{ top: flowH + 20, height: NODE_H }}>
              <span className="tg-icon">{ICONS.relay}</span>
              <span className="tg-text">
                <span className="tg-label">{link.label}</span>
                <span className="tg-detail">{link.detail} · runs for the whole mission</span>
              </span>
              <HeartPulse size={14} className="tg-lane-pulse" />
            </div>
          )}
        </>
      )}
    </div>
  );
}
