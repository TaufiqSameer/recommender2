import { useEffect, useState } from "react";
import { getActivityHistory } from "../services/api";
import type { ActivityHistoryResponse } from "../types/learning";
import { useAuth } from "../context/AuthContext";
import { Loader2, RefreshCw, CheckCircle, Circle, ChevronDown, ChevronUp } from "lucide-react";

type Activity = ActivityHistoryResponse["activities"][0];

function ActivityRow({ activity }: { activity: Activity }) {
  const [expanded, setExpanded] = useState(false);

  const scorePct = activity.score != null ? Math.round(activity.score * 100) : null;

  return (
    <div className={`history-row ${expanded ? "expanded" : ""}`}>
      <div className="history-row-main" onClick={() => setExpanded((e) => !e)}>
        <div className="history-status">
          {activity.completed
            ? <CheckCircle size={16} color="#22c55e" />
            : <Circle size={16} color="#475569" />}
        </div>

        <div className="history-info">
          <p className="history-title">{activity.title}</p>
          <p className="history-meta">
            <span className="skill-badge-sm">{activity.skill_label ?? activity.skill_id}</span>
            <span className="activity-type-badge">{activity.type}</span>
            <span className="difficulty-badge">{activity.difficulty}</span>
          </p>
        </div>

        <div className="history-score">
          {scorePct != null && (
            <span className={`score-badge ${scorePct >= 70 ? "good" : scorePct >= 40 ? "mid" : "low"}`}>
              {scorePct}%
            </span>
          )}
          <span className="history-date">
            {new Date(activity.created_at).toLocaleDateString()}
          </span>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div className="history-detail">
          <div className="detail-section">
            <p className="detail-label">Objective</p>
            <p>{activity.objective}</p>
          </div>
          <div className="detail-section">
            <p className="detail-label">Instructions</p>
            <p className="detail-instructions">{activity.instructions}</p>
          </div>
          {activity.hints && activity.hints.length > 0 && (
            <div className="detail-section">
              <p className="detail-label">Hints</p>
              <ul>
                {activity.hints.map((h: string, i: number) => <li key={i}>{h}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function History() {
  const { learnerId } = useAuth();
  const [data, setData] = useState<ActivityHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!learnerId) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getActivityHistory(learnerId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [learnerId]);

  if (loading) return (
    <div className="page-loading">
      <Loader2 className="spin" size={32} />
      <p>Loading your history...</p>
    </div>
  );

  if (error) return (
    <div className="page-error">
      <p>{error}</p>
      <button className="primary-button" onClick={load}><RefreshCw size={16} /> Retry</button>
    </div>
  );

  const activities = data?.activities ?? [];

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <p className="eyebrow">Your learning record</p>
          <h1>Activity History</h1>
        </div>
        <div className="page-header-meta">
          <span className="stat-chip">{data?.activities_completed ?? 0} completed</span>
          <button className="icon-button" onClick={load} title="Refresh">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="empty-state">
          <p>No learning history yet.</p>
          <p className="muted">Complete your first activity to start building your learning record.</p>
        </div>
      ) : (
        <div className="history-list">
          {activities.map((a: ActivityHistoryResponse["activities"][0]) => (
            <ActivityRow key={a.activity_id} activity={a} />
          ))}
        </div>
      )}
    </div>
  );
}
