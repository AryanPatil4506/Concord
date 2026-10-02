import { PlugZap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Briefing } from "./components/briefing/Briefing";
import { EvidenceView } from "./components/evidence/EvidenceView";
import { MethodView } from "./components/method/MethodView";
import { MissionView } from "./components/mission/MissionView";
import { Toasts } from "./components/shell/Toasts";
import { TopBar, type Route } from "./components/shell/TopBar";
import { Button, Modal, Spinner } from "./components/ui/ui";
import { useMission } from "./lib/mission";

const ROUTES: Route[] = ["console", "evidence", "method"];
const routeFromHash = (): Route => {
  const h = location.hash.replace("#/", "") as Route;
  return ROUTES.includes(h) ? h : "console";
};

export default function App() {
  const { store, actions } = useMission();
  const [route, setRoute] = useState<Route>(routeFromHash);
  const [confirmNew, setConfirmNew] = useState(false);

  useEffect(() => {
    const on = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  const go = useCallback((r: Route) => {
    if (location.hash !== `#/${r}`) history.pushState(null, "", `#/${r}`);
    setRoute(r);
    window.scrollTo({ top: 0 });
  }, []);

  const mission = store.mission;
  const newMission = () => {
    if (mission && mission.phase !== "complete") setConfirmNew(true);
    else {
      actions.end();
      go("console");
    }
  };

  return (
    <>
      <TopBar
        route={route}
        onRoute={go}
        connection={store.connection}
        hasMission={!!mission}
        onNewMission={newMission}
      />
      <main className="app-main">
        {route === "console" &&
          (mission ? (
            <MissionView key={`${mission.static.seed}-${mission.scenario}`} mission={mission} onNewMission={newMission} />
          ) : mission === null ? (
            <Briefing />
          ) : store.connection === "closed" ? (
            <EngineOffline />
          ) : (
            <div className="offline">
              <Spinner size={22} />
            </div>
          ))}
        {route === "evidence" && <EvidenceView />}
        {route === "method" && <MethodView />}
      </main>

      <Modal open={confirmNew} onClose={() => setConfirmNew(false)} width={440} label="End the current mission?">
        <div className="confirm">
          <h2>End the current mission?</h2>
          <p className="muted">The live mission stops and you go back to the briefing. Its decision log is not kept unless you finish the mission and download it.</p>
          <div className="confirm-actions">
            <Button variant="ghost" onClick={() => setConfirmNew(false)}>
              Keep flying
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                setConfirmNew(false);
                actions.end();
                go("console");
              }}
            >
              End mission
            </Button>
          </div>
        </div>
      </Modal>

      <Toasts notices={store.notices} onDismiss={actions.dismiss} />
    </>
  );
}

function EngineOffline() {
  return (
    <div className="offline">
      <div className="offline-card">
        <div className="offline-icon">
          <PlugZap size={20} />
        </div>
        <h1>The mission engine isn't running</h1>
        <p className="muted">
          The console is a live view of the CONCORD v0 simulator. Start it from the prototype folder — this page reconnects automatically.
        </p>
        <pre>cd prototype{"\n"}python -m server</pre>
        <p className="subtle">Evidence and Method work once the engine is up too.</p>
      </div>
    </div>
  );
}
