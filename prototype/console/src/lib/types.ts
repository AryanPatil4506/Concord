
export type Cell = [number, number];
export type AgentKind = "scout" | "cargo" | "rover" | "relay";
export type Phase = "running" | "paused" | "assessing" | "escalation" | "complete";
export type DisruptionKind =
  | "agent_fail"
  | "battery_drain"
  | "bridge_collapse"
  | "comm_blackout"
  | "storm"
  | "new_target";

export interface FleetSpec {
  id: string;
  kind: AgentKind;
  kind_label: string;
  caps: string[];
  speed: number;
  battery: number;
  comm: number;
  kits: number;
  aerial: boolean;
  sensor: number;
}

export interface StaticInfo {
  grid: { w: number; h: number };
  base: Cell;
  base_comm: number;
  sectors: Record<string, { x0: number; x1: number; y0: number; y1: number }>;
  tmax: number;
  seed: number;
  fleet: FleetSpec[];
  bridges: Cell[][];
  storm_hazard: number;
}

export interface PlanItem {
  label: string;
  pos: Cell;
  task: string | null;
}

export interface AgentState {
  id: string;
  kind: AgentKind;
  pos: Cell;
  batt: number;
  alive: boolean;
  conn: boolean;
  status: string;
  busy: number;
  kits: number;
  kit_cap: number;
  activity: string;
  plan: PlanItem[];
  route: Cell[];
  queued: number;
  queued_critical: number;
  energy: number;
  lost_t: number | null;
  lost_why: string | null;
  storm_exposed: boolean;
}

export interface SurvivorState {
  sid: string;
  pos: Cell;
  appear_t: number;
  detected_t: number | null;
  reported_t: number | null;
  delivered_t: number | null;
  by_call: boolean;
  assignee: string | null;
  sector: string | null;
}

export interface SurveyState {
  id: string;
  pos: Cell;
  status: "open" | "assigned" | "done" | "void";
  assignee: string | null;
}

export interface Storm {
  cx: number;
  cy: number;
  r: number;
  t_end: number;
}

export interface LiveMetrics {
  aided: number;
  awaiting: number;
  found: number;
  unreported: number;
  total: number;
  mean_tta: number | null;
  report_latency: number | null;
  agents_up: number;
  agents_total: number;
  lost_avoidable: number;
  lost_injected: number;
  surveyed: number;
  surveys_total: number;
  energy: number;
  reassignments: number;
  disruptions: number;
  decisions: number;
  connected: number;
}

export interface TickState {
  t: number;
  agents: AgentState[];
  survivors: SurvivorState[];
  surveys: SurveyState[];
  storm: Storm | null;
  relay_station: Cell | null;
  metrics: LiveMetrics;
}

export interface BidRow {
  task: string;
  label: string;
  winner: string;
  bid: number;
  via_base: boolean;
  eta: number;
  others: { agent: string; bid: number | null }[];
}

export type LogKind =
  | "event"
  | "relay"
  | "replan"
  | "assign"
  | "battery"
  | "voi"
  | "detect"
  | "report"
  | "deliver"
  | "loss"
  | "escalation"
  | "operator";

export interface LogEntry {
  i: number;
  t: number;
  kind: LogKind;
  text: string;
  agent?: string;
  sid?: string;
  bids?: BidRow[];
  released?: string[];
}

export interface ForecastPoint {
  t: number;
  p: number;
  kind: "periodic" | "assess";
}

export interface EscalationOption {
  key: string;
  title: string;
  detail: string;
  p: number;
  irreversible: boolean;
}

export interface Escalation {
  id: number;
  t: number;
  p_now: number;
  situation: string;
  options: EscalationOption[];
  recommend: string;
  timeout_s: number;
  remaining_s: number;
  k: number;
}

export interface InjectedEvent {
  t: number;
  kind: DisruptionKind;
  label: string;
  params: Record<string, unknown>;
  agent?: string | null;
}

export interface MissionMetrics {
  success: number;
  delivered_frac: number;
  survivors: number;
  time_to_aid: number;
  report_latency: number;
  agents_lost: number;
  agents_lost_non_injected: number;
  coverage: number;
  churn: number;
  energy: number;
  makespan: number;
  n_events: number;
  aid_times: (number | null)[];
}

export interface MissionSummary {
  metrics: MissionMetrics;
  baselines: { policy: string; name: string; metrics: MissionMetrics }[];
  escalations: { t: number; p_now: number; chosen: string; recommended: string; auto: boolean; title: string; p: number }[];
  injected: InjectedEvent[];
  disruptions: { t: number; kind: DisruptionKind; label: string }[];
  last_aid_t: number | null;
  replay: Record<string, unknown>;
}

export interface MissionSnapshot {
  scenario: string;
  scenario_title: string;
  objective: string;
  static: StaticInfo;
  terrain: number[][];
  dead: Cell[];
  bridges: boolean[];
  labels: Record<string, string>;
  phase: Phase;
  tps: number;
  base_tps: number;
  state: TickState;
  log: LogEntry[];
  timeline: ForecastPoint[];
  escalation: Escalation | null;
  injected: InjectedEvent[];
  summary: MissionSummary | null;
  escalate_below: number;
  cooldown_s: number;
  scheduled: number;
}

export type ServerMessage =
  | ({ type: "mission" } & MissionSnapshot)
  | { type: "idle" }
  | {
      type: "tick";
      state: TickState;
      log: LogEntry[];
      terrain?: number[][];
      bridges?: boolean[];
      dead?: Cell[];
      labels?: Record<string, string>;
    }
  | { type: "phase"; phase: Phase; reason?: string; escalation?: Escalation }
  | { type: "forecast"; t: number; p: number; kind: "periodic" | "assess" }
  | { type: "escalation_resolved"; key: string; auto: boolean }
  | { type: "speed"; tps: number }
  | { type: "injected"; event: InjectedEvent }
  | { type: "summary"; summary: MissionSummary }
  | { type: "notice"; level: "warning" | "error" | "info"; message: string };

export interface CompiledMission {
  objective: string;
  compiler: string;
  sectors: string[];
  horizon: number;
  nodes: {
    id: string;
    type: string;
    label: string;
    detail: string;
    requires: string;
    priority: number;
    sector?: string;
    continuous?: boolean;
  }[];
  edges: [string, string][];
  constraints: { label: string; value: string }[];
  checks: { label: string; ok: boolean }[];
  capabilities: Record<string, string[]>;
  task_count: number;
}

export interface ScenarioInfo {
  id: string;
  title: string;
  blurb: string;
  fixed_seed: number | null;
}
