import type { Escalation, ServerMessage } from "./types";

/**
 * Stands in for the engine's WebSocket in the static demo build. Missions are message streams the real
 * engine produced (`record_demo.py`); at an escalation each option leads to its own recorded branch.
 */
interface ReplayNode {
  messages: ServerMessage[];
  recommend?: string;
  branches?: Record<string, ReplayNode>;
}

const ASSESS_MS = 1400; // the live engine takes a few seconds per re-forecast
const SUMMARY_MS = 900;
const TIMEOUT_S = 30;

const cache = new Map<string, Promise<ReplayNode>>();
const load = (id: string) => {
  if (!cache.has(id)) {
    const p = fetch(`/demo/${id}.json`).then((r) => {
      if (!r.ok) throw new Error(String(r.status));
      return r.json() as Promise<ReplayNode>;
    });
    p.catch(() => cache.delete(id));
    cache.set(id, p);
  }
  return cache.get(id)!;
};

export class DemoEngine {
  private node: ReplayNode | null = null;
  private idx = 0;
  private run = false;
  private stepping = false;
  private waiting = false; // at an escalation
  private tps = 5;
  private baseTps = 5;
  private timer: number | undefined;
  private escTimer: number | undefined;
  private autoDecided = false;
  private finishing = false;
  private gen = 0;

  constructor(private emit: (m: ServerMessage) => void) {}

  connect() {
    this.emit({ type: "idle" });
  }

  async start(scenario: string) {
    this.stop();
    const gen = ++this.gen;
    let root: ReplayNode;
    try {
      root = await load(scenario);
    } catch {
      this.emit({ type: "notice", level: "error", message: "Couldn't load that recorded mission. Check your connection and try again." });
      this.emit({ type: "idle" });
      return;
    }
    if (gen !== this.gen) return;
    const [first, ...rest] = root.messages;
    if (first.type !== "mission") return;
    this.baseTps = first.base_tps;
    this.tps = first.tps;
    this.node = { ...root, messages: rest };
    this.idx = 0;
    this.emit(first);
    this.run = true;
    this.pump(0);
  }

  end() {
    this.stop();
    this.gen++;
    this.emit({ type: "idle" });
  }

  play() {
    if (!this.node || this.run || this.waiting || this.done()) return;
    this.run = true;
    this.emit({ type: "phase", phase: "running" });
    this.pump(0);
  }

  pause() {
    if (!this.run || this.waiting) return;
    this.run = false;
    this.emit({ type: "phase", phase: "paused" });
  }

  step() {
    if (!this.node || this.run || this.waiting || this.stepping) return;
    this.stepping = true;
    this.pump(0);
  }

  speed(mult: number) {
    this.tps = this.baseTps * Math.max(0.25, Math.min(8, mult));
    this.emit({ type: "speed", tps: this.tps });
  }

  decide(key: string, auto = false) {
    const node = this.node;
    if (!this.waiting || !node?.branches) return;
    const next = node.branches[key] ?? node.branches["*"];
    if (!next) return;
    window.clearTimeout(this.escTimer);
    this.waiting = false;
    this.autoDecided = auto;
    this.node = next;
    this.idx = 0;
    this.run = true;
    this.pump(0);
  }

  private done() {
    return !!this.node && this.idx >= this.node.messages.length && !this.node.branches;
  }

  private stop() {
    window.clearTimeout(this.timer);
    window.clearTimeout(this.escTimer);
    this.node = null;
    this.run = this.stepping = this.waiting = this.finishing = false;
  }

  private pump(delay: number) {
    window.clearTimeout(this.timer);
    const gen = this.gen;
    this.timer = window.setTimeout(() => gen === this.gen && this.advance(), delay);
  }

  /** Emit recorded messages until one that should take wall-clock time, then schedule the next. */
  private advance() {
    const node = this.node;
    if (!node || (!this.run && !this.stepping && !this.finishing)) return;
    let ticked = false;
    while (this.idx < node.messages.length) {
      const msg = this.patch(node.messages[this.idx]);
      if (msg.type === "tick" && ticked) break; // stepping: stop before the next tick
      this.idx++;
      if (msg.type === "phase") {
        if (msg.phase === "escalation" && msg.escalation) {
          this.emit({ ...msg, escalation: { ...msg.escalation, remaining_s: TIMEOUT_S } });
          this.waitForOperator(msg.escalation);
          return;
        }
        if (msg.phase === "running" || msg.phase === "paused") {
          this.emit({ type: "phase", phase: this.run ? "running" : "paused" });
          continue;
        }
        this.emit(msg);
        if (msg.phase === "assessing") return this.pump(ASSESS_MS);
        if (msg.phase === "complete") {
          // the engine runs the baselines before the summary arrives
          this.run = this.stepping = false;
          this.finishing = true;
          return this.pump(SUMMARY_MS);
        }
        continue;
      }
      this.emit(msg);
      if (msg.type === "tick") {
        if (this.stepping) {
          ticked = true;
          continue;
        }
        return this.pump(1000 / this.tps);
      }
    }
    this.stepping = this.finishing = false;
  }

  private waitForOperator(esc: Escalation) {
    this.waiting = true;
    this.autoDecided = false;
    this.run = this.stepping = false;
    const gen = this.gen;
    this.escTimer = window.setTimeout(() => gen === this.gen && this.decide(esc.recommend, true), TIMEOUT_S * 1000);
  }

  /** Recordings are made with an operator answering; reword them when the safe default applied instead. */
  private patch(msg: ServerMessage): ServerMessage {
    if (!this.autoDecided) return msg;
    if (msg.type === "escalation_resolved") return { ...msg, auto: true };
    if (msg.type === "tick" && msg.log.some((e) => e.kind === "operator")) {
      return {
        ...msg,
        log: msg.log.map((e) =>
          e.kind === "operator" ? { ...e, text: e.text.replace("Operator approved", "Safe default applied after 30 s without a response") } : e,
        ),
      };
    }
    if (msg.type === "summary") {
      const s = msg.summary;
      const last = s.escalations.length - 1;
      return {
        ...msg,
        summary: { ...s, escalations: s.escalations.map((e, i) => (i === last ? { ...e, auto: true } : e)) },
      };
    }
    return msg;
  }
}
