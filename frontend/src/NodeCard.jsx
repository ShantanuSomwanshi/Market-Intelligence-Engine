import { Handle, Position } from "reactflow";

const statusMap = {
  waiting: {
    border: "border-[#2b2f39]",
    glow: "",
    badge: "bg-[#5b6475]",
    chip: "text-[#9ca3af]",
  },
  running: {
    border: "border-[var(--accent)]",
    glow: "shadow-[0_0_0_1px_rgba(106,124,255,0.35),0_0_52px_rgba(106,124,255,0.22)] animate-nodePulse",
    badge: "bg-[var(--accent)]",
    chip: "text-accentSoft",
  },
  completed: {
    border: "border-[#29d37d]",
    glow: "shadow-[0_0_0_1px_rgba(41,211,125,0.24),0_0_34px_rgba(41,211,125,0.14)]",
    badge: "bg-[#29d37d]",
    chip: "text-[#bdf5d5]",
  },
  failed: {
    border: "border-[#ef4444]",
    glow: "shadow-[0_0_0_1px_rgba(239,68,68,0.24),0_0_28px_rgba(239,68,68,0.14)]",
    badge: "bg-[#ef4444]",
    chip: "text-[#fecaca]",
  },
  retrying: {
    border: "border-[#f59e0b]",
    glow: "shadow-[0_0_0_1px_rgba(245,158,11,0.22),0_0_30px_rgba(245,158,11,0.15)] animate-nodePulse",
    badge: "bg-[#f59e0b]",
    chip: "text-[#fde68a]",
  },
};

function NodeGlyph({ icon, status }) {
  return (
    <div
      className={`node-glyph-wrap flex h-12 w-12 items-center justify-center rounded-[18px] border border-white/8 bg-white/[0.04] ${
        status === "running" ? "glyph-live" : ""
      }`}
    >
      <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-glyph">{icon}</span>
    </div>
  );
}

export default function NodeCard({ data }) {
  const style = statusMap[data.status] || statusMap.waiting;

  return (
    <div
      className={`node-shell min-w-[240px] rounded-[26px] border bg-node px-4 py-4 text-left backdrop-blur-md transition-all duration-300 ${style.border} ${style.glow} ${
        data.isCurrent ? "node-current" : ""
      } ${data.isDimmed ? "node-dimmed" : ""}`}
      style={{ animationDelay: `${(data.index || 0) * 160}ms` }}
    >
      <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-black !bg-white" />
      <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-black !bg-white" />

      <div className="flex items-start justify-between gap-3">
        <NodeGlyph icon={data.icon} status={data.status} />
        <div className={`rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.3em] ${style.chip}`}>
          {data.status}
        </div>
      </div>

      <div className="mt-4">
        <div className="text-[1.02rem] font-semibold tracking-tight text-primary">{data.label}</div>
        <div className="mt-1 text-xs leading-5 text-secondary">{data.subtitle}</div>
      </div>

      <div className="mt-4 rounded-2xl border border-white/6 bg-white/[0.03] px-3 py-3">
        <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.28em] text-muted">
          <span>Module signal</span>
          <span>{String(data.status).slice(0, 3)}</span>
        </div>
        <div className="flex items-center gap-2 text-xs leading-5 text-muted">
          <span className={`h-2.5 w-2.5 rounded-full ${style.badge}`} />
          <span className="line-clamp-2">{data.detail || "Awaiting execution"}</span>
        </div>
        {data.status === "running" ? (
          <div className="mt-3 h-[2px] overflow-hidden rounded-full bg-white/[0.05]">
            <span className="node-scanline" />
          </div>
        ) : null}
      </div>
    </div>
  );
}
