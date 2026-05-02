import { useEffect, useState } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import NodeCard from "./NodeCard";

const nodeTypes = {
  workflowNode: NodeCard,
};

const glyphs = {
  input_node: "IN",
  web_research: "WEB",
  company_overview: "OVR",
  market_position: "MKT",
  competitor_mapping: "CMP",
  brand_activity: "BRD",
  events_footprint: "EVT",
  strategic_watchouts: "!",
  decision_makers: "DM",
  contact_intelligence: "@",
  outreach_generation: "MSG",
  tracking_logic: "TRK",
  validator: "OK",
  output: "OUT",
};

const subtitles = {
  input_node: "Input capture",
  web_research: "Source crawl",
  company_overview: "Business profile",
  market_position: "Perception scan",
  competitor_mapping: "Competitive landscape",
  brand_activity: "Recent motions",
  events_footprint: "Experience signals",
  strategic_watchouts: "Strategic tensions",
  decision_makers: "Stakeholder fit",
  contact_intelligence: "Public verification",
  outreach_generation: "Fact-grounded messaging",
  tracking_logic: "Demo metrics",
  validator: "Quality gate",
  output: "JSON handoff",
};

const positions = {
  input_node: { x: 80, y: 270 },
  web_research: { x: 410, y: 150 },
  company_overview: { x: 720, y: 150 },
  market_position: { x: 1030, y: 150 },
  competitor_mapping: { x: 720, y: 395 },
  brand_activity: { x: 1030, y: 395 },
  events_footprint: { x: 1340, y: 395 },
  strategic_watchouts: { x: 1340, y: 150 },
  decision_makers: { x: 1655, y: 150 },
  contact_intelligence: { x: 1655, y: 395 },
  outreach_generation: { x: 1985, y: 260 },
  tracking_logic: { x: 2315, y: 260 },
  validator: { x: 2645, y: 150 },
  output: { x: 2645, y: 395 },
};

function buildFlow(graph, run) {
  const runNodes = run?.nodes || [];
  const runNodeMap = Object.fromEntries(runNodes.map((node) => [node.id, node]));
  const currentNodeId = run?.current_node_id;
  const orderedIds = Object.keys(positions);
  const runProgress = runNodes.length
    ? runNodes.filter((node) => node.status === "completed").length / runNodes.length
    : 0;

  const nodes = (graph.nodes || []).map((node) => {
    const stateNode = runNodeMap[node.id];
    const status = stateNode?.status || node.status || "waiting";

    return {
      id: node.id,
      type: "workflowNode",
      draggable: false,
      selectable: false,
      position: positions[node.id] || { x: 0, y: 0 },
      data: {
        icon: glyphs[node.id] || "•",
        label: node.label,
        subtitle: subtitles[node.id] || "Pipeline node",
        status,
        detail: stateNode?.detail || "",
        isCurrent: currentNodeId === node.id,
        index: orderedIds.indexOf(node.id),
        isDimmed: Boolean(currentNodeId) && currentNodeId !== node.id && status === "waiting",
      },
    };
  });

  const nodeStatusMap = Object.fromEntries(nodes.map((node) => [node.id, node.data.status]));
  const edges = (graph.edges || []).map((edge) => {
    const sourceStatus = nodeStatusMap[edge.source];
    const targetStatus = nodeStatusMap[edge.target];
    const isRunningPath = targetStatus === "running";
    const isCompletedPath = sourceStatus === "completed" && targetStatus === "completed";
    const isRetry = edge.kind === "retry";

    let stroke = "rgba(114, 126, 155, 0.22)";
    if (isCompletedPath) stroke = "rgba(41, 211, 125, 0.74)";
    if (isRunningPath) stroke = "rgba(106, 124, 255, 0.96)";
    if (isRetry) stroke = "rgba(245, 158, 11, 0.84)";

    return {
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      animated: isRunningPath || isRetry,
      className: isRunningPath
        ? "flow-edge-running"
        : isRetry
          ? "flow-edge-retry"
          : isCompletedPath
            ? "flow-edge-complete"
            : "flow-edge-idle",
      style: {
        stroke,
        strokeWidth: isRunningPath ? 2.9 : isCompletedPath ? 2.2 : 1.7,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: stroke,
      },
    };
  });

  return { nodes, edges, runProgress };
}

export default function PipelineGraph({ graph, run, theme }) {
  const [flow, setFlow] = useState({ nodes: [], edges: [], runProgress: 0 });

  useEffect(() => {
    setFlow(buildFlow(graph, run));
  }, [graph, run]);

  return (
    <section className="glass-panel command-stage relative min-h-[720px] flex-1 overflow-hidden rounded-[34px] p-0">
      <div className="command-stage-grid" />
      <div className="pointer-events-none absolute inset-0">
        <div className="command-stage-stars" />
        <div className="command-stage-beam" />
        <div className="canvas-aura canvas-aura-one" />
        <div className="canvas-aura canvas-aura-two" />
        <div className="canvas-aura canvas-aura-three" />
      </div>

      <div className="absolute inset-x-0 top-0 z-10 flex items-center justify-between border-b border-skin-line bg-stageOverlay px-5 py-4 backdrop-blur-xl">
        <div>
          <div className="text-[10px] uppercase tracking-[0.34em] text-muted">Command Center</div>
          <h2 className="mt-1 text-xl font-semibold text-primary">Execution Matrix</h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="glass-chip px-3 py-1.5 text-primary">Progress {Math.round((flow.runProgress || 0) * 100)}%</span>
          <span className="glass-chip px-3 py-1.5">Waiting</span>
          <span className="glass-chip text-accentSoft px-3 py-1.5">Running</span>
          <span className="glass-chip px-3 py-1.5 text-[#baf7d0]">Completed</span>
          <span className="glass-chip px-3 py-1.5 text-[#fde68a]">Retrying</span>
          <span className="glass-chip px-3 py-1.5 text-[#fecaca]">Failed</span>
          <span className="glass-chip px-3 py-1.5">{theme === "obsidian" ? "Neon Black" : "Titanium Grey"}</span>
        </div>
      </div>

      <div className="absolute left-5 right-5 top-[78px] z-[5] h-[3px] overflow-hidden rounded-full bg-white/[0.04]">
        <span className="progress-trace" style={{ width: `${Math.max((flow.runProgress || 0) * 100, 6)}%` }} />
      </div>

      <div className="absolute inset-0 pt-[86px]">
        <ReactFlow
          fitView
          fitViewOptions={{ padding: 0.18 }}
          nodes={flow.nodes}
          edges={flow.edges}
          nodeTypes={nodeTypes}
          minZoom={0.42}
          maxZoom={1.45}
          panOnScroll
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            gap={24}
            size={1.1}
            color={theme === "obsidian" ? "rgba(255,255,255,0.045)" : "rgba(15,23,42,0.08)"}
          />
          <Controls
            showInteractive={false}
            className="!rounded-2xl !border !border-[var(--line)] !bg-[var(--panel-elevated)] !shadow-none"
          />
        </ReactFlow>
      </div>
    </section>
  );
}
