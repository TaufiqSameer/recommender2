import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import { getProgress, type ProgressResponse } from "../services/api";
import { Loader2, TrendingUp, Award, BookOpen, Flame, RefreshCw } from "lucide-react";

export default function Progress() {
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setData(await getProgress());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load progress.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="page-loading">
      <Loader2 className="spin" size={32} />
      <p>Loading your progress...</p>
    </div>
  );

  if (error) return (
    <div className="page-error">
      <p>{error}</p>
      <button className="primary-button" onClick={load}>
        <RefreshCw size={16} /> Retry
      </button>
    </div>
  );

  if (!data) return null;

  // Aggregate timeline by date for the line chart
  const timelineMap: Record<string, number[]> = {};
  for (const ev of data.evidence_timeline) {
    if (!timelineMap[ev.date]) timelineMap[ev.date] = [];
    timelineMap[ev.date].push(ev.score);
  }
  const timelineData = Object.entries(timelineMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, scores]) => ({
      date,
      mastery: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100),
    }));

  const skillData = data.skill_mastery.slice(0, 10).map((s) => ({
    name: s.label.length > 18 ? s.label.slice(0, 18) + "…" : s.label,
    mastery: Math.round(s.mastery * 100),
    status: s.status,
  }));

  const masteryPct = Math.round(data.overall_mastery * 100);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <p className="eyebrow">Your learning analytics</p>
          <h1>Progress</h1>
        </div>
        <button className="icon-button" onClick={load} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Stat cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <TrendingUp size={20} className="stat-icon" />
          <p className="stat-label">Overall mastery</p>
          <p className="stat-value">{masteryPct}%</p>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${masteryPct}%` }} />
          </div>
        </div>

        <div className="stat-card">
          <Award size={20} className="stat-icon" />
          <p className="stat-label">Skills mastered</p>
          <p className="stat-value">{data.skills_mastered}</p>
          <p className="stat-description">{data.skills_learning} still learning</p>
        </div>

        <div className="stat-card">
          <BookOpen size={20} className="stat-icon" />
          <p className="stat-label">Activities done</p>
          <p className="stat-value">{data.activities_completed}</p>
          <p className="stat-description">Keep going!</p>
        </div>

        <div className="stat-card">
          <Flame size={20} className="stat-icon" />
          <p className="stat-label">Day streak</p>
          <p className="stat-value">{data.streak_days}</p>
          <p className="stat-description">{data.streak_days > 0 ? "🔥 Keep it up!" : "Start your streak today"}</p>
        </div>
      </div>

      {/* Mastery over time */}
      <div className="chart-card">
        <h2 className="chart-title">Mastery over time</h2>
        {timelineData.length === 0 ? (
          <div className="empty-state">
            <p>No learning history yet.</p>
            <p className="muted">Complete your first activity to see your progress chart.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(139,92,246,0.15)" />
              <XAxis dataKey="date" stroke="#a78bfa" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} stroke="#a78bfa" tick={{ fontSize: 11 }} unit="%" />
              <Tooltip
                contentStyle={{ background: "#1e1232", border: "1px solid #4c1d95", borderRadius: 8 }}
                labelStyle={{ color: "#e9d5ff" }}
                itemStyle={{ color: "#a78bfa" }}
              />
              <Line
                type="monotone"
                dataKey="mastery"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ fill: "#8b5cf6", r: 4 }}
                activeDot={{ r: 6 }}
                name="Avg score %"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Skill mastery breakdown */}
      <div className="chart-card">
        <h2 className="chart-title">Skill mastery</h2>
        {skillData.length === 0 ? (
          <div className="empty-state">
            <p>No skills tracked yet.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, skillData.length * 36)}>
            <BarChart data={skillData} layout="vertical">
              <XAxis type="number" domain={[0, 100]} stroke="#a78bfa" tick={{ fontSize: 11 }} unit="%" />
              <YAxis type="category" dataKey="name" stroke="#a78bfa" tick={{ fontSize: 11 }} width={140} />
              <Tooltip
                contentStyle={{ background: "#1e1232", border: "1px solid #4c1d95", borderRadius: 8 }}
                labelStyle={{ color: "#e9d5ff" }}
                itemStyle={{ color: "#a78bfa" }}
              />
              <Bar dataKey="mastery" fill="#7c3aed" radius={[0, 4, 4, 0]} name="Mastery %" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
