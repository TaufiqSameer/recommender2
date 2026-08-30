import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Lightbulb,
  Loader2,
  PlusCircle,
  RefreshCw,
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Code2,
  Target,
  Compass,
  TrendingUp,
  Bot,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  createChatSession,
  getChatSession,
  getChatSessions,
  getNextActivity,
  sendChatSessionMessage,
  submitActivity,
} from "../services/api";
import type { NextActivityResponse, Evaluation } from "../types/learning";
import { useAuth } from "../context/AuthContext";

type Message = {
  id: string;
  role: "assistant" | "user";
  content: string;
  created_at?: string;
};

type LearnProps = {
  onBack: () => void;
};

export default function Learn({ onBack }: LearnProps) {
  const { learnerId } = useAuth();

  const [activity, setActivity] = useState<NextActivityResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [answer, setAnswer] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sendingChat, setSendingChat] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [learnerMastery, setLearnerMastery] = useState<number | null>(null);
  const [hintsExpanded, setHintsExpanded] = useState(false);
  const [mobileTab, setMobileTab] = useState<"workspace" | "tutor">("workspace");

  const chatEndRef = useRef<HTMLDivElement>(null);
  const solutionRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sendingChat]);

  // Load or restore active session + recommended activity
  async function initLearnSession() {
    if (!learnerId) return;
    try {
      setLoading(true);
      setError(null);

      // 1. Fetch current recommended activity
      const activityRes = await getNextActivity(learnerId);
      setActivity(activityRes);
      setEvaluation(null);

      // 2. Fetch existing chat sessions or create a new one
      const sessionsRes = await getChatSessions();
      let activeSessionId = sessionsRes.sessions[0]?.id;

      if (activeSessionId) {
        const sessionDetail = await getChatSession(activeSessionId);
        setSessionId(activeSessionId);
        if (sessionDetail.messages && sessionDetail.messages.length > 0) {
          setMessages(
            sessionDetail.messages.map((m) => ({
              id: m.id,
              role: m.role as "assistant" | "user",
              content: m.content,
              created_at: m.created_at,
            })),
          );
        } else {
          setMessages([
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `Welcome to **${activityRes.skill.label}**! I'm your AI learning tutor. I've prepared a ${activityRes.activity.difficulty} challenge for you. How can I help you work through it?`,
            },
          ]);
        }
      } else {
        const newSession = await createChatSession(
          `Learning ${activityRes.skill.label}`,
        );
        setSessionId(newSession.id);
        setMessages([
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `Welcome! Let's explore **${activityRes.skill.label}**. Feel free to ask questions, request hints, or brainstorm your solution with me.`,
          },
        ]);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to initialize learning session.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    initLearnSession();
  }, [learnerId]);

  // Start fresh chat thread
  async function handleNewChat() {
    if (!activity) return;
    try {
      setLoading(true);
      const newSession = await createChatSession(
        `Learning ${activity.skill.label}`,
      );
      setSessionId(newSession.id);
      setMessages([
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Fresh conversation started for **${activity.skill.label}**. What would you like to explore or clarify?`,
        },
      ]);
    } catch {
      setError("Failed to create a new conversation thread.");
    } finally {
      setLoading(false);
    }
  }

  // Send message to persistent chat session
  async function handleChatMessage(customText?: string) {
    const text = (customText ?? chatInput).trim();
    if (!text || sendingChat || submitting || !sessionId) return;

    if (!customText) setChatInput("");
    setError(null);

    // Optimistic UI update
    const tempId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: tempId, role: "user", content: text },
    ]);

    setSendingChat(true);

    try {
      const res = await sendChatSessionMessage(
        sessionId,
        text,
        activity?.activity_id,
      );

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempId),
        {
          id: res.user_message.id,
          role: "user",
          content: res.user_message.content,
        },
        {
          id: res.assistant_message.id,
          role: "assistant",
          content: res.assistant_message.content,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "EurekaAI is temporarily unavailable. Your progress is safe. Please try again in a moment.",
        },
      ]);
    } finally {
      setSendingChat(false);
    }
  }

  // Submit exercise solution
  async function handleSubmit() {
    if (!activity || !answer.trim() || submitting || sendingChat || !learnerId)
      return;

    const submittedAnswer = answer.trim();
    setSubmitting(true);
    setError(null);

    try {
      const result = await submitActivity(
        learnerId,
        activity.activity_id,
        submittedAnswer,
      );

      setEvaluation(result.evaluation);
      setLearnerMastery(result.learner_state.mastery);

      // Append notice to chat history
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "user",
          content: `📝 *[Submitted Solution for Evaluation]*`,
        },
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `🎯 **Solution Evaluated: ${Math.round(
            result.evaluation.score * 100,
          )}% Score!**\n\n${result.evaluation.feedback}\n\nYour updated mastery for **${
            activity.skill.label
          }** is **${Math.round(result.learner_state.mastery * 100)}%**.`,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to evaluate your solution.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  // Advance to next recommended activity
  async function handleLoadNextActivity() {
    if (!learnerId) return;
    try {
      setLoading(true);
      setError(null);
      const nextRes = await getNextActivity(learnerId);
      setActivity(nextRes);
      setEvaluation(null);
      setAnswer("");
      setHintsExpanded(false);

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `🚀 Ready for the next challenge! Loaded: **${nextRes.activity.title}** (${nextRes.activity.difficulty}). Let's dive in!`,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load the next recommended activity.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleChatMessage();
    }
  }

  if (loading) {
    return (
      <div className="learn-page">
        <div className="learn-loading-card">
          <Loader2 size={36} className="spin" />
          <h2>Preparing Your Adaptive Session</h2>
          <p>Analyzing mastery graph and calibrating challenge difficulty...</p>
        </div>
      </div>
    );
  }

  if (error && !activity) {
    return (
      <div className="learn-page">
        <div className="learn-error-card">
          <AlertCircle size={40} color="#ef4444" />
          <h2>Unable to Load Activity</h2>
          <p>{error}</p>
          <div className="learn-error-actions">
            <button className="primary-button" onClick={initLearnSession}>
              <RefreshCw size={16} /> Retry
            </button>
            <button className="secondary-button" onClick={onBack}>
              <ArrowLeft size={16} /> Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="learn-page">
      {/* Top Header Bar */}
      <header className="learn-top-bar">
        <div className="learn-nav-left">
          <button className="learn-back-btn" onClick={onBack} title="Back to Dashboard">
            <ArrowLeft size={16} />
            <span>Dashboard</span>
          </button>
          <div className="learn-breadcrumb-divider">/</div>
          <div className="learn-skill-tag">
            <Compass size={15} />
            <span>{activity?.skill.label ?? "Skill Learning"}</span>
          </div>
        </div>

        <div className="learn-nav-right">
          {learnerMastery !== null && (
            <div className="learn-mastery-chip">
              <TrendingUp size={14} />
              <span>Mastery: <strong>{Math.round(learnerMastery * 100)}%</strong></span>
            </div>
          )}

          <button className="learn-new-thread-btn" onClick={handleNewChat} title="Start new conversation thread">
            <PlusCircle size={15} />
            <span>New Thread</span>
          </button>
        </div>
      </header>

      {/* Mobile Tab Switcher */}
      <div className="learn-mobile-tabs">
        <button
          className={`mobile-tab-btn ${mobileTab === "workspace" ? "active" : ""}`}
          onClick={() => setMobileTab("workspace")}
        >
          <Code2 size={16} />
          <span>Challenge & Solution</span>
        </button>
        <button
          className={`mobile-tab-btn ${mobileTab === "tutor" ? "active" : ""}`}
          onClick={() => setMobileTab("tutor")}
        >
          <Bot size={16} />
          <span>AI Tutor ({messages.length})</span>
        </button>
      </div>

      {/* Main Split Workspace */}
      <div className="learn-workspace-grid">
        {/* Left Column: Challenge & Solution */}
        <div className={`learn-challenge-column ${mobileTab === "workspace" ? "mobile-show" : "mobile-hide"}`}>
          {activity && (
            <div className="challenge-card">
              {/* Activity Header */}
              <div className="challenge-header">
                <div className="challenge-badges">
                  <span className="badge-type">{activity.activity.type.replace(/_/g, " ")}</span>
                  <span className={`badge-difficulty ${activity.activity.difficulty.toLowerCase()}`}>
                    {activity.activity.difficulty}
                  </span>
                  <span className="badge-skill">{activity.skill.label}</span>
                </div>
                <h1 className="challenge-title">{activity.activity.title}</h1>
              </div>

              {/* Objective Box */}
              <div className="challenge-objective-box">
                <Target size={18} className="objective-icon" />
                <div>
                  <strong>Learning Objective</strong>
                  <p>{activity.activity.objective}</p>
                </div>
              </div>

              {/* Instructions */}
              <div className="challenge-instructions-box">
                <div className="section-label">Instructions</div>
                <div className="instructions-body">
                  {activity.activity.instructions.split("\n").map((line, idx) => (
                    <p key={idx}>{line}</p>
                  ))}
                </div>
              </div>

              {/* Recommender Reason */}
              <div className="recommender-insight-box">
                <Sparkles size={18} className="sparkle-icon" />
                <div>
                  <strong>Why this challenge?</strong>
                  <p>{activity.recommendation.reason}</p>
                </div>
              </div>

              {/* Hints Accordion */}
              {activity.activity.hints && activity.activity.hints.length > 0 && (
                <div className="hints-accordion">
                  <button
                    className="hints-toggle-btn"
                    onClick={() => setHintsExpanded(!hintsExpanded)}
                  >
                    <div className="hints-toggle-left">
                      <Lightbulb size={16} className="hint-bulb-icon" />
                      <span>Hints & Guidance ({activity.activity.hints.length})</span>
                    </div>
                    {hintsExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  {hintsExpanded && (
                    <div className="hints-dropdown-body">
                      {activity.activity.hints.map((hint, idx) => (
                        <div key={idx} className="hint-item">
                          <span className="hint-num">#{idx + 1}</span>
                          <p>{hint}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Solution Workspace */}
              {!evaluation ? (
                <div className="solution-workspace-box">
                  <div className="solution-header">
                    <div className="solution-header-left">
                      <Code2 size={17} />
                      <strong>Your Solution</strong>
                    </div>
                    <span className="solution-hint-tag">Write explanation, code, or answers</span>
                  </div>

                  <textarea
                    ref={solutionRef}
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder="Enter your solution, code, or explanation here... (Ctrl + Enter to submit)"
                    rows={7}
                    disabled={submitting || sendingChat}
                    className="solution-textarea"
                  />

                  <div className="solution-footer">
                    <span className="keyboard-shortcut-hint">
                      Press <strong>Ctrl + Enter</strong> to submit for evaluation
                    </span>
                    <button
                      className="primary-button solution-submit-btn"
                      onClick={handleSubmit}
                      disabled={!answer.trim() || submitting || sendingChat}
                    >
                      {submitting ? (
                        <>
                          <Loader2 size={16} className="spin" />
                          <span>Evaluating Solution...</span>
                        </>
                      ) : (
                        <>
                          <Send size={16} />
                          <span>Submit Solution</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                /* Evaluation Breakdown Card */
                <div className="evaluation-card">
                  <div className="eval-card-header">
                    <div className="eval-score-badge">
                      <CheckCircle2 size={24} color="#22c55e" />
                      <div>
                        <span className="eval-label">Evaluation Complete</span>
                        <h3>Score: {Math.round(evaluation.score * 100)}%</h3>
                      </div>
                    </div>
                    {learnerMastery !== null && (
                      <div className="eval-mastery-update">
                        <span>Updated Mastery</span>
                        <strong>{Math.round(learnerMastery * 100)}%</strong>
                      </div>
                    )}
                  </div>

                  <div className="eval-feedback-text">
                    <p>{evaluation.feedback}</p>
                  </div>

                  {evaluation.strengths && evaluation.strengths.length > 0 && (
                    <div className="eval-section strengths">
                      <div className="eval-section-title">
                        <CheckCircle2 size={15} color="#22c55e" />
                        <span>Key Strengths</span>
                      </div>
                      <ul>
                        {evaluation.strengths.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {evaluation.weaknesses && evaluation.weaknesses.length > 0 && (
                    <div className="eval-section weaknesses">
                      <div className="eval-section-title">
                        <AlertCircle size={15} color="#f59e0b" />
                        <span>Areas to Strengthen</span>
                      </div>
                      <ul>
                        {evaluation.weaknesses.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {evaluation.next_step && (
                    <div className="eval-next-step">
                      <strong>Next Step: </strong>
                      <span>{evaluation.next_step}</span>
                    </div>
                  )}

                  <div className="eval-actions-bar">
                    <button className="primary-button next-activity-btn" onClick={handleLoadNextActivity}>
                      <span>Next Recommended Challenge</span>
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: AI Tutor Companion */}
        <div className={`learn-tutor-column ${mobileTab === "tutor" ? "mobile-show" : "mobile-hide"}`}>
          <div className="tutor-card">
            <div className="tutor-header">
              <div className="tutor-header-title">
                <div className="tutor-avatar-badge">
                  <Sparkles size={16} />
                </div>
                <div>
                  <strong>EurekaAI Tutor</strong>
                  <span className="tutor-status-pill">● Online Companion</span>
                </div>
              </div>
            </div>

            {/* Quick Prompt Chips */}
            <div className="tutor-quick-prompts">
              <button
                className="quick-chip"
                onClick={() => handleChatMessage("Can you give me a subtle hint to point me in the right direction?")}
                disabled={sendingChat || submitting}
              >
                💡 Hint
              </button>
              <button
                className="quick-chip"
                onClick={() => handleChatMessage("Could you explain this concept with a brief real-world example?")}
                disabled={sendingChat || submitting}
              >
                🔍 Example
              </button>
              <button
                className="quick-chip"
                onClick={() => handleChatMessage("What are the most common mistakes or pitfalls for this topic?")}
                disabled={sendingChat || submitting}
              >
                ⚠️ Pitfalls
              </button>
            </div>

            {/* Messages Feed */}
            <div className="tutor-messages-scroll">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`tutor-msg-bubble ${
                    message.role === "user" ? "user-msg" : "assistant-msg"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="tutor-msg-avatar">
                      <Sparkles size={14} />
                    </div>
                  )}
                  <div className="tutor-msg-content">
                    <div className="tutor-msg-sender">
                      {message.role === "assistant" ? "EurekaAI" : "You"}
                    </div>
                    <div className="tutor-msg-text">
                      {message.content.split("\n").map((line, i) => (
                        <p key={i}>{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}

              {sendingChat && (
                <div className="tutor-msg-bubble assistant-msg">
                  <div className="tutor-msg-avatar">
                    <Sparkles size={14} />
                  </div>
                  <div className="tutor-msg-content typing">
                    <span /><span /><span />
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Tutor Input Bar */}
            <div className="tutor-composer">
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your tutor anything or request guidance..."
                rows={2}
                disabled={sendingChat || submitting}
                className="tutor-textarea"
              />
              <div className="tutor-composer-footer">
                <span className="composer-hint">Enter to send · Shift+Enter new line</span>
                <button
                  className="tutor-send-btn"
                  onClick={() => handleChatMessage()}
                  disabled={!chatInput.trim() || sendingChat || submitting}
                  aria-label="Send Message"
                >
                  {sendingChat ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}