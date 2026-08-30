import { Suspense, useMemo, useRef, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, Float } from "@react-three/drei";
import * as THREE from "three";
import { getSkillGraph, type GraphResponse } from "../services/api";
import {
  Loader2,
  RefreshCw,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Box,
  Layers,
  Sparkles,
  CheckCircle2,
  CircleDot,
  Lock,
  Compass,
} from "lucide-react";

// ─── Status colors ────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  mastered: "#22c55e",
  learning: "#a855f7",
  available: "#6366f1",
  locked: "#475569",
};

const STATUS_EMISSIVE: Record<string, string> = {
  mastered: "#15803d",
  learning: "#7e22ce",
  available: "#4338ca",
  locked: "#1e293b",
};

function statusLabel(s: string): string {
  return (
    {
      mastered: "Mastered",
      learning: "Learning",
      available: "Available",
      locked: "Locked",
    }[s] ?? s
  );
}

// ─── 3D Node Positioning ──────────────────────────────────────────────────────

type Node3D = {
  id: string;
  label: string;
  domain: string;
  difficulty: number;
  mastery: number;
  status: string;
  attempts: number;
  position: [number, number, number];
};

function compute3DLayout(graph: GraphResponse): {
  nodes: Node3D[];
  nodeMap: Record<string, Node3D>;
} {
  const inDegree: Record<string, number> = {};
  for (const n of graph.nodes) inDegree[n.id] = 0;
  for (const e of graph.edges) {
    inDegree[e.target] = (inDegree[e.target] ?? 0) + 1;
  }

  const layers: string[][] = [];
  const placed = new Set<string>();
  let remaining = graph.nodes.map((n) => n.id);

  while (remaining.length > 0) {
    const layer = remaining.filter(
      (id) => (inDegree[id] ?? 0) === 0 && !placed.has(id),
    );
    if (layer.length === 0) {
      layers.push(remaining.filter((id) => !placed.has(id)));
      break;
    }
    layers.push(layer);
    for (const id of layer) {
      placed.add(id);
      for (const e of graph.edges) {
        if (e.source === id) inDegree[e.target]--;
      }
    }
    remaining = remaining.filter((id) => !placed.has(id));
  }

  const nodes: Node3D[] = [];
  const nodeMap: Record<string, Node3D> = {};
  const numLayers = Math.max(layers.length, 1);
  const xSpan = 16;
  const xStep = numLayers > 1 ? xSpan / (numLayers - 1) : 0;
  const xStart = -xSpan / 2;

  layers.forEach((layer, col) => {
    const layerSize = layer.length;
    const ySpan = Math.min(layerSize * 2.2, 10);
    const yStep = layerSize > 1 ? ySpan / (layerSize - 1) : 0;
    const yStart = (layerSize - 1) * (yStep / 2);

    layer.forEach((id, row) => {
      const node = graph.nodes.find((n) => n.id === id);
      if (!node) return;

      const x = xStart + col * xStep;
      const y = yStart - row * yStep;
      // Stagger in Z depth for visual richness
      const z = Math.sin(col * 1.5 + row * 0.8) * 1.8;

      const node3d: Node3D = {
        ...node,
        position: [x, y, z],
      };
      nodes.push(node3d);
      nodeMap[id] = node3d;
    });
  });

  return { nodes, nodeMap };
}

// ─── 3D Node Mesh Component ───────────────────────────────────────────────────

function SkillSphere({
  node,
  isSelected,
  onClick,
}: {
  node: Node3D;
  isSelected: boolean;
  onClick: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const color = STATUS_COLORS[node.status] ?? STATUS_COLORS.locked;
  const emissive = STATUS_EMISSIVE[node.status] ?? STATUS_EMISSIVE.locked;

  useFrame((_, delta) => {
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * (hovered ? 2.5 : 0.8);
    }
  });

  const scale = isSelected ? 1.35 : hovered ? 1.2 : 1.0;

  return (
    <Float speed={1.2} rotationIntensity={0.2} floatIntensity={0.3}>
      <group position={node.position}>
        {/* Outer Halo Ring */}
        <mesh ref={ringRef} scale={scale * 1.35}>
          <ringGeometry args={[0.55, 0.65, 32]} />
          <meshBasicMaterial
            color={color}
            side={THREE.DoubleSide}
            transparent
            opacity={isSelected ? 0.9 : hovered ? 0.7 : 0.35}
          />
        </mesh>

        {/* Central Core Sphere */}
        <mesh
          ref={meshRef}
          scale={scale}
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(true);
            document.body.style.cursor = "pointer";
          }}
          onPointerOut={() => {
            setHovered(false);
            document.body.style.cursor = "auto";
          }}
        >
          <sphereGeometry args={[0.48, 32, 32]} />
          <meshStandardMaterial
            color={color}
            emissive={emissive}
            emissiveIntensity={isSelected ? 0.9 : hovered ? 0.7 : 0.4}
            roughness={0.25}
            metalness={0.6}
          />
        </mesh>

        {/* Floating HTML Badge */}
        <Html
          position={[0, -0.75, 0]}
          center
          distanceFactor={14}
          style={{ pointerEvents: "none" }}
        >
          <div
            className={`node-3d-badge ${isSelected ? "selected" : ""} ${
              hovered ? "hovered" : ""
            }`}
            style={{
              borderColor: color,
              boxShadow: isSelected ? `0 0 16px ${color}` : undefined,
            }}
          >
            <div className="node-3d-title">{node.label}</div>
            <div className="node-3d-sub" style={{ color }}>
              {statusLabel(node.status)} · {Math.round(node.mastery * 100)}%
            </div>
          </div>
        </Html>
      </group>
    </Float>
  );
}

// ─── 3D Curved Edge Component ─────────────────────────────────────────────────

function SkillLink({
  start,
  end,
  isHighlighted,
}: {
  start: [number, number, number];
  end: [number, number, number];
  isHighlighted: boolean;
}) {
  const curve = useMemo(() => {
    const p1 = new THREE.Vector3(...start);
    const p2 = new THREE.Vector3(...end);
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    mid.z += 0.8; // subtle curve outward
    return new THREE.QuadraticBezierCurve3(p1, mid, p2);
  }, [start, end]);

  const points = useMemo(() => curve.getPoints(24), [curve]);
  const geometry = useMemo(
    () => new THREE.BufferGeometry().setFromPoints(points),
    [points],
  );

  return (
    <primitive
      object={
        new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({
            color: isHighlighted ? 0xa855f7 : 0x6366f1,
            transparent: true,
            opacity: isHighlighted ? 0.85 : 0.25,
            linewidth: isHighlighted ? 2 : 1,
          }),
        )
      }
    />
  );
}

// ─── 3D Scene Container ───────────────────────────────────────────────────────

function Scene3D({
  graph,
  selectedId,
  onSelectNode,
  autoRotate,
}: {
  graph: GraphResponse;
  selectedId: string | null;
  onSelectNode: (id: string) => void;
  autoRotate: boolean;
}) {
  const { nodes, nodeMap } = useMemo(() => compute3DLayout(graph), [graph]);

  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[10, 15, 10]} intensity={1.2} />
      <pointLight position={[0, 0, 8]} color="#c4b5fd" intensity={1.5} />
      <pointLight position={[-10, -5, -5]} color="#7c3aed" intensity={1.2} />

      <OrbitControls
        enableDamping
        dampingFactor={0.06}
        maxDistance={32}
        minDistance={6}
        autoRotate={autoRotate}
        autoRotateSpeed={0.6}
      />

      {/* Render Edges */}
      {graph.edges.map((e, i) => {
        const s = nodeMap[e.source];
        const t = nodeMap[e.target];
        if (!s || !t) return null;
        const isHighlighted =
          selectedId === e.source || selectedId === e.target;
        return (
          <SkillLink
            key={i}
            start={s.position}
            end={t.position}
            isHighlighted={isHighlighted}
          />
        );
      })}

      {/* Render Nodes */}
      {nodes.map((node) => (
        <SkillSphere
          key={node.id}
          node={node}
          isSelected={selectedId === node.id}
          onClick={() => onSelectNode(node.id)}
        />
      ))}
    </>
  );
}

// ─── 2D SVG Graph Fallback ────────────────────────────────────────────────────

type NodeLayout2D = {
  id: string;
  x: number;
  y: number;
  label: string;
  mastery: number;
  status: string;
};

function layoutNodes2D(graph: GraphResponse): NodeLayout2D[] {
  const inDegree: Record<string, number> = {};
  for (const n of graph.nodes) inDegree[n.id] = 0;
  for (const e of graph.edges) {
    inDegree[e.target] = (inDegree[e.target] ?? 0) + 1;
  }

  const layers: string[][] = [];
  const placed = new Set<string>();
  let remaining = graph.nodes.map((n) => n.id);

  while (remaining.length > 0) {
    const layer = remaining.filter(
      (id) => (inDegree[id] ?? 0) === 0 && !placed.has(id),
    );
    if (layer.length === 0) {
      layers.push(remaining.filter((id) => !placed.has(id)));
      break;
    }
    layers.push(layer);
    for (const id of layer) {
      placed.add(id);
      for (const e of graph.edges) {
        if (e.source === id) inDegree[e.target]--;
      }
    }
    remaining = remaining.filter((id) => !placed.has(id));
  }

  const nodeMap: Record<string, NodeLayout2D> = {};
  const W = 175;
  const H = 90;
  const PAD_X = 80;
  const PAD_Y = 50;

  layers.forEach((layer, col) => {
    layer.forEach((id, row) => {
      const node = graph.nodes.find((n) => n.id === id);
      if (!node) return;
      nodeMap[id] = {
        id,
        x: PAD_X + col * W,
        y: PAD_Y + row * H,
        label: node.label,
        mastery: node.mastery,
        status: node.status,
      };
    });
  });

  return Object.values(nodeMap);
}

function SVGGraph({
  graph,
  onNodeClick,
  selectedId,
}: {
  graph: GraphResponse;
  onNodeClick: (id: string) => void;
  selectedId: string | null;
}) {
  const layouts = useMemo(() => layoutNodes2D(graph), [graph]);
  const layoutMap: Record<string, NodeLayout2D> = useMemo(
    () => Object.fromEntries(layouts.map((l) => [l.id, l])),
    [layouts],
  );

  const maxX = Math.max(...layouts.map((l) => l.x), 500) + 140;
  const maxY = Math.max(...layouts.map((l) => l.y), 300) + 70;

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });

  return (
    <div className="graph-container">
      <div className="graph-controls">
        <button
          className="icon-button"
          onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
          title="Zoom in"
        >
          <ZoomIn size={16} />
        </button>
        <button
          className="icon-button"
          onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
          title="Zoom out"
        >
          <ZoomOut size={16} />
        </button>
        <button
          className="icon-button"
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          title="Reset"
        >
          <RotateCcw size={16} />
        </button>
      </div>

      <svg
        width="100%"
        height="540"
        viewBox={`${-pan.x / zoom} ${-pan.y / zoom} ${maxX / zoom} ${
          maxY / zoom
        }`}
        style={{ cursor: dragging ? "grabbing" : "grab" }}
        onMouseDown={(e) => {
          setDragging(true);
          setLastMouse({ x: e.clientX, y: e.clientY });
        }}
        onMouseMove={(e) => {
          if (!dragging) return;
          setPan((p) => ({
            x: p.x + (e.clientX - lastMouse.x),
            y: p.y + (e.clientY - lastMouse.y),
          }));
          setLastMouse({ x: e.clientX, y: e.clientY });
        }}
        onMouseUp={() => setDragging(false)}
        onMouseLeave={() => setDragging(false)}
      >
        <defs>
          <marker
            id="arrow"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(139,92,246,0.6)" />
          </marker>
        </defs>

        {/* Edges */}
        {graph.edges.map((e, i) => {
          const s = layoutMap[e.source];
          const t = layoutMap[e.target];
          if (!s || !t) return null;
          return (
            <line
              key={i}
              x1={s.x + 65}
              y1={s.y + 22}
              x2={t.x}
              y2={t.y + 22}
              stroke="rgba(139,92,246,0.4)"
              strokeWidth={1.5}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Nodes */}
        {layouts.map((n) => {
          const color = STATUS_COLORS[n.status] ?? STATUS_COLORS.locked;
          const isSelected = selectedId === n.id;
          return (
            <g
              key={n.id}
              onClick={() => onNodeClick(n.id)}
              style={{ cursor: "pointer" }}
            >
              <rect
                x={n.x}
                y={n.y}
                width={125}
                height={46}
                rx={8}
                fill={
                  isSelected
                    ? "rgba(139,92,246,0.35)"
                    : "rgba(26,19,48,0.92)"
                }
                stroke={isSelected ? "#c4b5fd" : color}
                strokeWidth={isSelected ? 2 : 1.5}
              />
              <rect
                x={n.x + 4}
                y={n.y + 38}
                width={117 * n.mastery}
                height={4}
                rx={2}
                fill={color}
                opacity={0.8}
              />
              <text
                x={n.x + 8}
                y={n.y + 17}
                fill="#f5f3ff"
                fontSize={11}
                fontWeight="600"
              >
                {n.label.length > 15 ? n.label.slice(0, 15) + "…" : n.label}
              </text>
              <text x={n.x + 8} y={n.y + 31} fill={color} fontSize={9}>
                {statusLabel(n.status)} · {Math.round(n.mastery * 100)}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ─── Node Inspector Panel ─────────────────────────────────────────────────────

function NodePanel({
  graph,
  nodeId,
  onClose,
}: {
  graph: GraphResponse;
  nodeId: string;
  onClose: () => void;
}) {
  const node = graph.nodes.find((n) => n.id === nodeId);
  if (!node) return null;

  const prereqs = graph.edges
    .filter((e) => e.target === nodeId)
    .map((e) => graph.nodes.find((n) => n.id === e.source))
    .filter(Boolean);

  const nextSkills = graph.edges
    .filter((e) => e.source === nodeId)
    .map((e) => graph.nodes.find((n) => n.id === e.target))
    .filter(Boolean);

  const color = STATUS_COLORS[node.status] ?? STATUS_COLORS.locked;

  return (
    <div className="node-panel">
      <button className="node-panel-close" onClick={onClose}>
        ✕
      </button>
      <div className="node-panel-header">
        <span
          className="node-chip-status"
          style={{ background: `${color}22`, color, borderColor: color }}
        >
          {statusLabel(node.status)}
        </span>
        <span className="node-diff-badge">Level {node.difficulty}</span>
      </div>

      <h3 style={{ color: "#f5f3ff", marginTop: "0.5rem" }}>{node.label}</h3>

      <div className="node-mastery-bar">
        <span>Current Mastery</span>
        <strong>{Math.round(node.mastery * 100)}%</strong>
      </div>
      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${node.mastery * 100}%`, background: color }}
        />
      </div>

      {prereqs.length > 0 && (
        <div className="node-section">
          <p className="node-section-label">Prerequisites</p>
          <div className="node-chips-list">
            {prereqs.map(
              (p) =>
                p && (
                  <div
                    key={p.id}
                    className="node-chip"
                    style={{ borderColor: STATUS_COLORS[p.status] }}
                  >
                    {p.mastery >= 0.8 ? (
                      <CheckCircle2 size={13} color="#22c55e" />
                    ) : (
                      <CircleDot size={13} color={STATUS_COLORS[p.status]} />
                    )}
                    <span>{p.label}</span>
                  </div>
                ),
            )}
          </div>
        </div>
      )}

      {nextSkills.length > 0 && (
        <div className="node-section">
          <p className="node-section-label">Unlocks</p>
          <div className="node-chips-list">
            {nextSkills.map(
              (n) =>
                n && (
                  <div
                    key={n.id}
                    className="node-chip"
                    style={{ borderColor: STATUS_COLORS[n.status] }}
                  >
                    {n.status === "locked" ? (
                      <Lock size={12} color="#64748b" />
                    ) : (
                      <Sparkles size={12} color="#a855f7" />
                    )}
                    <span>{n.label}</span>
                  </div>
                ),
            )}
          </div>
        </div>
      )}

      <div className="node-meta-grid">
        <div className="meta-card">
          <span className="meta-label">Domain</span>
          <span className="meta-val">{node.domain}</span>
        </div>
        <div className="meta-card">
          <span className="meta-label">Attempts</span>
          <span className="meta-val">{node.attempts}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Legend ───────────────────────────────────────────────────────────────────

function Legend() {
  return (
    <div className="graph-legend">
      {Object.entries(STATUS_COLORS).map(([s, c]) => (
        <div key={s} className="legend-item">
          <div className="legend-dot" style={{ background: c }} />
          <span>{statusLabel(s)}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Roadmap Page ────────────────────────────────────────────────────────

export default function Roadmap() {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"3d" | "2d">("3d");
  const [autoRotate, setAutoRotate] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setGraph(await getSkillGraph());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skill graph.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading)
    return (
      <div className="page-loading">
        <Loader2 className="spin" size={32} />
        <p>Generating your adaptive skill universe...</p>
      </div>
    );

  if (error)
    return (
      <div className="page-error">
        <p>{error}</p>
        <button className="primary-button" onClick={load}>
          <RefreshCw size={16} /> Retry
        </button>
      </div>
    );

  if (!graph || graph.nodes.length === 0)
    return (
      <div className="page-content">
        <div className="page-header">
          <div>
            <p className="eyebrow">Your learning path</p>
            <h1>Skill Roadmap</h1>
          </div>
        </div>
        <div className="empty-state">
          <Compass size={40} className="empty-icon" />
          <p>No skill graph available yet.</p>
          <p className="muted">
            Complete onboarding so EurekaAI can build your interactive skill roadmap.
          </p>
        </div>
      </div>
    );

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <p className="eyebrow">Interactive Skill DAG</p>
          <h1>Skill Roadmap</h1>
        </div>
        <div className="roadmap-actions">
          {/* 3D vs 2D Toggle */}
          <div className="view-mode-toggle">
            <button
              className={`toggle-btn ${viewMode === "3d" ? "active" : ""}`}
              onClick={() => setViewMode("3d")}
              title="3D Universe"
            >
              <Box size={16} />
              <span>3D Galaxy</span>
            </button>
            <button
              className={`toggle-btn ${viewMode === "2d" ? "active" : ""}`}
              onClick={() => setViewMode("2d")}
              title="2D Flowchart"
            >
              <Layers size={16} />
              <span>2D Flow</span>
            </button>
          </div>

          <button className="icon-button" onClick={load} title="Refresh graph">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      <div className="graph-wrapper">
        <Legend />

        <div className="graph-and-panel">
          {viewMode === "3d" ? (
            <div className="canvas-3d-wrapper">
              <div className="canvas-3d-controls">
                <button
                  className={`canvas-pill-btn ${autoRotate ? "active" : ""}`}
                  onClick={() => setAutoRotate((r) => !r)}
                >
                  {autoRotate ? "⏸ Pause Rotation" : "▶ Auto Rotate"}
                </button>
              </div>

              <Suspense
                fallback={
                  <div className="page-loading">
                    <Loader2 className="spin" size={32} />
                  </div>
                }
              >
                <Canvas
                  camera={{ position: [0, 0, 18], fov: 45 }}
                  style={{ background: "#0c0817", borderRadius: "12px" }}
                >
                  <Scene3D
                    graph={graph}
                    selectedId={selectedNode}
                    onSelectNode={(id) =>
                      setSelectedNode(id === selectedNode ? null : id)
                    }
                    autoRotate={autoRotate}
                  />
                </Canvas>
              </Suspense>
            </div>
          ) : (
            <SVGGraph
              graph={graph}
              onNodeClick={(id) =>
                setSelectedNode(id === selectedNode ? null : id)
              }
              selectedId={selectedNode}
            />
          )}

          {selectedNode && (
            <NodePanel
              graph={graph}
              nodeId={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          )}
        </div>
      </div>

      <p className="graph-hint">
        {viewMode === "3d"
          ? "Left click + drag to rotate · Right click to pan · Scroll to zoom · Click node to inspect details"
          : "Click a node to inspect · Drag to pan · Scroll to zoom"}
      </p>
    </div>
  );
}
