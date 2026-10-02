"""FastAPI + WebSocket server for the CONCORD mission console (`python -m server`)."""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import compiler, forecasting  # noqa: E402
from .session import SCENARIOS, MissionSession  # noqa: E402

RESULTS = os.path.join(HERE, "results")
DIST = os.path.join(HERE, "console", "dist")


class Hub:

    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.session: MissionSession | None = None

    async def broadcast(self, msg):
        data = json.dumps(msg, default=_json_default)
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)

    async def new_session(self, scenario, seed, objective, sectors):
        if self.session:
            await self.session.stop()
        self.session = MissionSession(self.broadcast, scenario=scenario, seed=seed, objective=objective)
        if sectors:
            for tk in self.session.world.tasks.values():
                if tk.kind == "survey" and tk.id[3] not in sectors:
                    tk.status = "void"
        self.session.start()
        await self.broadcast(self.session.full_state())

    async def end_session(self):
        if self.session:
            await self.session.stop()
        self.session = None
        await self.broadcast(dict(type="idle"))


def _json_default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


hub = Hub()


@asynccontextmanager
async def lifespan(_app):
    loop = asyncio.get_running_loop()
    # warm the worker pool so the first forecast is not slowed by process start-up
    await asyncio.gather(*[loop.run_in_executor(forecasting.pool(), abs, i) for i in range(8)])
    yield
    if hub.session:
        await hub.session.stop()
    forecasting.shutdown()


app = FastAPI(title="CONCORD live console", lifespan=lifespan)


class CompileRequest(BaseModel):
    text: str = ""
    scenario: str = "storyboard"


@app.get("/api/health")
def health():
    return dict(ok=True, engine="concord_v0", mission=hub.session is not None)


@app.get("/api/scenarios")
def scenarios():
    return [dict(id=k, title=v["title"], blurb=v["blurb"], fixed_seed=v["seed"]) for k, v in SCENARIOS.items()]


@app.post("/api/compile")
def compile_mission(req: CompileRequest):
    tmax = SCENARIOS.get(req.scenario, SCENARIOS["storyboard"])["tmax"]
    return compiler.compile_objective(req.text, tmax=tmax)


@app.get("/api/default-objective")
def default_objective():
    return dict(text=compiler.DEFAULT_OBJECTIVE)


@app.get("/api/evidence")
def evidence():
    with open(os.path.join(RESULTS, "summary.json")) as f:
        summary = json.load(f)
    out = dict(main=summary["main"], stress=summary["stress"], ablation=summary["ablation"],
               paired=summary["paired_concord_minus_greedy"])
    sb = os.path.join(RESULTS, "storyboard.json")
    if os.path.exists(sb):
        with open(sb) as f:
            s = json.load(f)
        out["storyboard"] = dict(metrics=s["metrics"], timeline=s["timeline"], escalation=s["escalation"])
    return JSONResponse(out)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    hub.clients.add(ws)
    try:
        await ws.send_text(json.dumps(hub.session.full_state() if hub.session else dict(type="idle"),
                                      default=_json_default))
        while True:
            msg = json.loads(await ws.receive_text())
            await handle(ws, msg)
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(ws)


async def handle(ws, msg):
    kind = msg.get("type")
    s = hub.session
    if kind == "start":
        scen = msg.get("scenario", "storyboard")
        if scen not in SCENARIOS:
            return
        seed = msg.get("seed")
        await hub.new_session(scen, int(seed) if seed not in (None, "") else None, msg.get("objective", ""),
                              msg.get("sectors"))
        if msg.get("autoplay", True):
            await hub.session.play()
        return
    if kind == "end":
        await hub.end_session()
        return
    if s is None:
        return
    if kind == "play":
        await s.play()
    elif kind == "pause":
        await s.pause()
    elif kind == "step":
        await s.step_once()
    elif kind == "speed":
        await s.set_speed(msg.get("mult", 1))
    elif kind == "inject":
        err = await s.inject(msg.get("kind"), msg.get("params"))
        if err:
            await ws.send_text(json.dumps(dict(type="notice", level="warning", message=err)))
    elif kind == "decide":
        await s.decide(msg.get("key"))


if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = os.path.join(DIST, path)
        if path and os.path.isfile(f):
            return FileResponse(f)
        return FileResponse(os.path.join(DIST, "index.html"))
