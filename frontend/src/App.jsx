import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import InputForm from "./InputForm";
import PipelineGraph from "./PipelineGraph";
import ReportViewer from "./ReportViewer";

const defaultGraph = {
  nodes: [],
  edges: [],
};

const defaultForm = {
  company_name: "",
  category_description: "",
};

function AnimatedNumber({ value, suffix = "" }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let frame = 0;
    const totalFrames = 26;
    const timer = window.setInterval(() => {
      frame += 1;
      const progress = Math.min(frame / totalFrames, 1);
      setDisplay(Math.round(value * progress));
      if (progress >= 1) {
        window.clearInterval(timer);
      }
    }, 26);

    return () => window.clearInterval(timer);
  }, [value]);

  return (
    <span>
      {display}
      {suffix}
    </span>
  );
}

function CommandPalette({ open, onClose, onThemeChange, onDemoFill }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/55 px-4 pt-[12vh] backdrop-blur-xl">
      <div className="bg-panelElevated w-full max-w-2xl rounded-[30px] border border-skin-line p-4 shadow-shell">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-[0.32em] text-muted">Command Palette</div>
            <h3 className="mt-2 text-xl font-semibold text-primary">Control the AI cockpit</h3>
          </div>
          <button type="button" onClick={onClose} className="glass-chip px-3 py-2 text-sm text-secondary">
            Esc
          </button>
        </div>

        <div className="grid gap-3">
          <button type="button" onClick={onDemoFill} className="command-item">
            <span className="command-dot bg-[var(--accent)]" />
            Fill demo company input
          </button>
          <button type="button" onClick={() => onThemeChange("obsidian")} className="command-item">
            <span className="command-dot bg-[var(--accent)]" />
            Switch to black neon mode
          </button>
          <button type="button" onClick={() => onThemeChange("graphite")} className="command-item">
            <span className="command-dot bg-emerald-400" />
            Switch to grey lab mode
          </button>
          <div className="command-item cursor-default">
            <span className="command-dot bg-violet-400" />
            Live workflow and report drawer respond automatically to backend events
          </div>
        </div>
      </div>
    </div>
  );
}

function HologramOrb({ connectionState }) {
  return (
    <div className="orb-shell">
      <div className="orb-halo orb-halo-a" />
      <div className="orb-halo orb-halo-b" />
      <div className="orb-core">
        <div className="orb-ring orb-ring-a" />
        <div className="orb-ring orb-ring-b" />
        <div className="orb-ring orb-ring-c" />
        <div className="orb-center">
          <div className="text-[10px] uppercase tracking-[0.34em] text-muted">System</div>
          <div className="mt-2 text-lg font-semibold text-primary">{connectionState === "live" ? "SYNCED" : "STANDBY"}</div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState("obsidian");
  const [formValues, setFormValues] = useState(defaultForm);
  const [graph, setGraph] = useState(defaultGraph);
  const [latestRun, setLatestRun] = useState(null);
  const [connectionState, setConnectionState] = useState("connecting");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [now, setNow] = useState(new Date());
  const [commandOpen, setCommandOpen] = useState(false);
  const [cursorGlow, setCursorGlow] = useState({ x: 35, y: 22 });
  const deferredRun = useDeferredValue(latestRun);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((current) => !current);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    const onPointerMove = (event) => {
      const x = (event.clientX / window.innerWidth) * 100;
      const y = (event.clientY / window.innerHeight) * 100;
      setCursorGlow({ x, y });
    };
    window.addEventListener("pointermove", onPointerMove);
    return () => window.removeEventListener("pointermove", onPointerMove);
  }, []);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [graphResponse, runsResponse] = await Promise.all([fetch("/api/graph"), fetch("/api/runs")]);

        if (graphResponse.ok) {
          const graphPayload = await graphResponse.json();
          startTransition(() => setGraph(graphPayload));
        }

        if (runsResponse.ok) {
          const runsPayload = await runsResponse.json();
          if (runsPayload.length > 0) {
            const latest = await fetch(`/api/runs/${runsPayload[0].run_id}`);
            if (latest.ok) {
              const latestPayload = await latest.json();
              startTransition(() => setLatestRun(latestPayload));
            }
          }
        }
      } catch (_error) {
        setConnectionState("offline");
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

    socket.onopen = () => setConnectionState("live");
    socket.onclose = () => setConnectionState("offline");
    socket.onerror = () => setConnectionState("offline");
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      startTransition(() => {
        if (payload.graph) {
          setGraph((current) => ({ ...current, ...payload.graph }));
        }
        if (payload.run) {
          setLatestRun(payload.run);
        }
      });
    };

    return () => socket.close();
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!formValues.company_name.trim() || !formValues.category_description.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formValues),
      });

      if (response.ok) {
        const payload = await response.json();
        startTransition(() => setLatestRun(payload));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  function fillDemoInput() {
    setFormValues({
      company_name: "Notion",
      category_description: "Collaborative productivity software for teams",
    });
    setCommandOpen(false);
  }

  const stats = useMemo(
    () => [
      { label: "AI Sections", value: 10, suffix: "" },
      { label: "Pipeline Nodes", value: graph.nodes?.length || 14, suffix: "" },
      { label: "Retry Guard", value: 3, suffix: "x" },
      { label: "Live Channels", value: 24, suffix: "/7" },
    ],
    [graph.nodes]
  );

  const completedNodes = latestRun?.nodes?.filter((node) => node.status === "completed").length || 0;
  const runStatusLabel = latestRun?.status || "idle";
  const clockLabel = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <>
      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        onThemeChange={setTheme}
        onDemoFill={fillDemoInput}
      />

      <main
        className="min-h-screen bg-app px-4 py-4 text-primary transition-colors duration-300 md:px-6"
        style={
          {
            "--cursor-x": `${cursorGlow.x}%`,
            "--cursor-y": `${cursorGlow.y}%`,
          }
        }
      >
        <div className="ambient-grid" />
        <div className="cursor-spotlight" />

        <div className="bg-panel mx-auto flex min-h-[calc(100vh-2rem)] max-w-[1880px] flex-col overflow-visible rounded-[34px] border border-skin-line shadow-shell backdrop-blur-2xl">
          <header className="relative overflow-hidden border-b border-skin-line px-5 py-5 md:px-7">
            <div className="hero-noise" />
            <div className="hero-aurora hero-aurora-a" />
            <div className="hero-aurora hero-aurora-b" />

            <div className="relative z-10 flex flex-col gap-8">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                
                  <div className="status-pulse">
                    <span className="status-dot" />
                    AI Pipeline Active
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <div className="glass-chip px-3 py-2 text-xs text-secondary">{clockLabel}</div>
                  <div className="glass-chip px-3 py-2 text-xs text-secondary">
                    {connectionState === "live" ? "Realtime uplink stable" : connectionState}
                  </div>
                  <button type="button" onClick={() => setCommandOpen(true)} className="glass-chip px-3 py-2 text-xs text-secondary">
                    Ctrl+K
                  </button>
                  <div className="bg-panelElevated flex items-center gap-1 rounded-full border border-skin-line p-1">
                    <button
                      type="button"
                      onClick={() => setTheme("obsidian")}
                      className={`rounded-full px-3 py-2 text-xs font-medium transition ${
                        theme === "obsidian" ? "bg-accent text-black" : "text-muted hover:text-primary"
                      }`}
                    >
                      Black
                    </button>
                    <button
                      type="button"
                      onClick={() => setTheme("graphite")}
                      className={`rounded-full px-3 py-2 text-xs font-medium transition ${
                        theme === "graphite" ? "bg-slate-300 text-slate-900" : "text-muted hover:text-primary"
                      }`}
                    >
                      Grey
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid gap-8 xl:grid-cols-[1.45fr_0.95fr] xl:items-center">
                <div className="hero-copy stagger-fade">
                  <div className="mb-3 text-[11px] uppercase tracking-[0.36em] text-muted">
                    Autonomous Market Intelligence Operating System
                  </div>
                  <h1 className="hero-title max-w-4xl text-4xl font-semibold leading-[0.94] tracking-[-0.04em] md:text-6xl xl:text-[5.4rem]">
                    The <span className="hero-gradient-text">future-ready AI cockpit</span> for market intelligence and outreach.
                  </h1>
                  <p className="mt-5 max-w-3xl text-base leading-7 text-secondary md:text-lg">
                    A premium command center where research, validation, decision-maker discovery, and outreach flow
                    through a live autonomous graph. Built to feel like 2035 arrived early.
                  </p>

                  <div className="mt-7 flex flex-wrap gap-3">
                    <div className="hero-chip">
                      <span className="hero-chip-label">Run Status</span>
                      <span className="hero-chip-value">{runStatusLabel}</span>
                    </div>
                    <div className="hero-chip">
                      <span className="hero-chip-label">Nodes Completed</span>
                      <span className="hero-chip-value">{completedNodes}</span>
                    </div>
                    <div className="hero-chip">
                      <span className="hero-chip-label">Thinking Mode</span>
                      <span className="hero-chip-value">LangGraph Live</span>
                    </div>
                  </div>
                </div>

                <div className="grid gap-5 xl:justify-items-end">
                  <HologramOrb connectionState={connectionState} />
                  <div className="thinking-card stagger-fade">
                    <div className="text-[10px] uppercase tracking-[0.34em] text-muted">AI Thinking</div>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-secondary">
                      Monitoring source aggregation, reasoning chains, contact verification, and output confidence in
                      real time.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {stats.map((item, index) => (
                  <div key={item.label} className="premium-stat stagger-fade" style={{ animationDelay: `${index * 120}ms` }}>
                    <div className="premium-stat-label">{item.label}</div>
                    <div className="premium-stat-value">
                      <AnimatedNumber value={item.value} suffix={item.suffix} />
                    </div>
                    <div className="premium-stat-trace" />
                  </div>
                ))}
              </div>
            </div>
          </header>

          <div className="flex flex-1 flex-col gap-5 overflow-hidden p-4 md:p-5">
            <InputForm
              values={formValues}
              onChange={handleChange}
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
              currentRun={latestRun}
              onOpenCommand={() => setCommandOpen(true)}
            />

            <PipelineGraph graph={graph} run={latestRun} theme={theme} />
          </div>

          <ReportViewer run={deferredRun} />
        </div>
      </main>
    </>
  );
}
