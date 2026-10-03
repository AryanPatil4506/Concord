import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef, type ReactNode } from "react";
import { DEMO } from "./api";
import { DemoEngine } from "./demo";
import type { DisruptionKind, MissionSnapshot, ServerMessage } from "./types";

export type Connection = "connecting" | "open" | "closed";

export interface Notice {
  id: number;
  level: "warning" | "error" | "info" | "success";
  message: string;
}

export interface MissionStore {
  connection: Connection;
  /** null = no mission running (show the briefing) ; undefined = not yet known */
  mission: MissionSnapshot | null | undefined;
  assessing: string | null;
  escalationReceivedAt: number;
  notices: Notice[];
  lastInjectAt: number;
}

type Action =
  | { type: "connection"; value: Connection }
  | { type: "message"; msg: ServerMessage }
  | { type: "notice"; notice: Omit<Notice, "id"> }
  | { type: "dismiss"; id: number }
  | { type: "injected-local" };

let noticeId = 1;

function reducer(s: MissionStore, a: Action): MissionStore {
  switch (a.type) {
    case "connection":
      return { ...s, connection: a.value };
    case "notice":
      return { ...s, notices: [...s.notices.slice(-3), { ...a.notice, id: noticeId++ }] };
    case "dismiss":
      return { ...s, notices: s.notices.filter((n) => n.id !== a.id) };
    case "injected-local":
      return { ...s, lastInjectAt: Date.now() };
    case "message":
      return applyMessage(s, a.msg);
  }
}

function applyMessage(s: MissionStore, msg: ServerMessage): MissionStore {
  if (msg.type === "idle") return { ...s, mission: null, assessing: null };
  if (msg.type === "mission") {
    const { type: _t, ...snap } = msg;
    return { ...s, mission: snap, assessing: null, escalationReceivedAt: Date.now() };
  }
  if (msg.type === "notice") {
    return { ...s, notices: [...s.notices.slice(-3), { id: noticeId++, level: msg.level, message: msg.message }] };
  }
  const m = s.mission;
  if (!m) return s;
  switch (msg.type) {
    case "tick": {
      const seen = m.log.length ? m.log[m.log.length - 1].i : -1;
      const fresh = msg.log.filter((e) => e.i > seen);
      return {
        ...s,
        mission: {
          ...m,
          state: msg.state,
          log: fresh.length ? [...m.log, ...fresh] : m.log,
          terrain: msg.terrain ?? m.terrain,
          bridges: msg.bridges ?? m.bridges,
          dead: msg.dead ?? m.dead,
          labels: msg.labels ?? m.labels,
        },
      };
    }
    case "phase":
      return {
        ...s,
        assessing: msg.phase === "assessing" ? msg.reason ?? "Re-forecasting" : null,
        escalationReceivedAt: msg.escalation ? Date.now() : s.escalationReceivedAt,
        mission: { ...m, phase: msg.phase, escalation: msg.escalation ?? (msg.phase === "escalation" ? m.escalation : null) },
      };
    case "forecast":
      return { ...s, mission: { ...m, timeline: [...m.timeline, { t: msg.t, p: msg.p, kind: msg.kind }] } };
    case "escalation_resolved":
      return { ...s, mission: { ...m, escalation: null } };
    case "speed":
      return { ...s, mission: { ...m, tps: msg.tps } };
    case "injected":
      return { ...s, mission: { ...m, injected: [...m.injected, msg.event] } };
    case "summary":
      return { ...s, mission: { ...m, summary: msg.summary } };
  }
  return s;
}

export interface StartOptions {
  scenario: string;
  seed?: number | null;
  objective: string;
  sectors?: string[];
}

export interface MissionActions {
  start: (o: StartOptions) => void;
  end: () => void;
  play: () => void;
  pause: () => void;
  step: () => void;
  speed: (mult: number) => void;
  inject: (kind: DisruptionKind, params?: Record<string, unknown>) => void;
  decide: (key: string) => void;
  notify: (n: Omit<Notice, "id">) => void;
  dismiss: (id: number) => void;
}

const Ctx = createContext<{ store: MissionStore; actions: MissionActions } | null>(null);

function wsUrl() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws`;
}

export function MissionProvider({ children }: { children: ReactNode }) {
  const [store, dispatch] = useReducer(reducer, {
    connection: "connecting",
    mission: undefined,
    assessing: null,
    escalationReceivedAt: 0,
    notices: [],
    lastInjectAt: 0,
  });
  const wsRef = useRef<WebSocket | null>(null);
  const demoRef = useRef<DemoEngine | null>(null);

  useEffect(() => {
    if (DEMO) {
      const engine = new DemoEngine((msg) => dispatch({ type: "message", msg }));
      demoRef.current = engine;
      dispatch({ type: "connection", value: "open" });
      engine.connect();
      return () => engine.end();
    }
    let closed = false;
    let retry: number | undefined;
    let attempt = 0;
    const connect = () => {
      dispatch({ type: "connection", value: "connecting" });
      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;
      ws.onopen = () => {
        attempt = 0;
        dispatch({ type: "connection", value: "open" });
      };
      ws.onmessage = (ev) => dispatch({ type: "message", msg: JSON.parse(ev.data) as ServerMessage });
      ws.onclose = () => {
        if (closed) return;
        dispatch({ type: "connection", value: "closed" });
        retry = window.setTimeout(connect, Math.min(4000, 500 * 2 ** attempt++));
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  const send = useCallback((msg: Record<string, unknown>) => {
    const demo = demoRef.current;
    if (demo) {
      switch (msg.type) {
        case "start":
          return void demo.start(msg.scenario as string);
        case "end":
          return demo.end();
        case "play":
          return demo.play();
        case "pause":
          return demo.pause();
        case "step":
          return demo.step();
        case "speed":
          return demo.speed(msg.mult as number);
        case "decide":
          return demo.decide(msg.key as string);
      }
      return;
    }
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }, []);

  const actions = useMemo<MissionActions>(
    () => ({
      start: (o) => send({ type: "start", ...o }),
      end: () => send({ type: "end" }),
      play: () => send({ type: "play" }),
      pause: () => send({ type: "pause" }),
      step: () => send({ type: "step" }),
      speed: (mult) => send({ type: "speed", mult }),
      inject: (kind, params) => {
        send({ type: "inject", kind, params: params ?? {} });
        dispatch({ type: "injected-local" });
      },
      decide: (key) => send({ type: "decide", key }),
      notify: (notice) => dispatch({ type: "notice", notice }),
      dismiss: (id) => dispatch({ type: "dismiss", id }),
    }),
    [send],
  );

  const value = useMemo(() => ({ store, actions }), [store, actions]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMission() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useMission outside MissionProvider");
  return v;
}
