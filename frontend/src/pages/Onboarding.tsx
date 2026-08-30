import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Send, Sparkles, HelpCircle } from "lucide-react";
import {
  completeOnboarding,
  getOnboardingStatus,
  sendOnboardingChat,
  submitAssessmentAnswer,
  type AssessmentQuestion,
  type OnboardingChatResponse,
} from "../services/api";
import { useAuth } from "../context/AuthContext";

type Msg = { role: "user" | "assistant"; content: string };

const STATE_LABELS: Record<string, string> = {
  NEW: "Getting started",
  DISCOVERING_GOAL: "Understanding your goals",
  DISCOVERING_INTERESTS: "Exploring your interests",
  DISCOVERING_BACKGROUND: "Learning about your background",
  ASSESSMENT: "Initial assessment",
  PROFILE_READY: "Profile complete",
  LEARNING: "Ready to learn",
};

const WELCOME =
  "Hi! I'm LearnAI. I'm here to build your personalised learning path. To get started — what would you like to learn?";

export default function Onboarding() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: WELCOME },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [state, setState] = useState("DISCOVERING_GOAL");
  const [progress, setProgress] = useState(0);
  const [assessmentQ, setAssessmentQ] = useState<AssessmentQuestion | null>(null);
  const [assessmentAnswer, setAssessmentAnswer] = useState("");
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, assessmentQ, sending]);

  const appendMessage = useCallback((msg: Msg) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  function applyResponse(res: OnboardingChatResponse) {
    setState(res.state);
    setProgress(res.progress);
    if (res.message) {
      appendMessage({ role: "assistant", content: res.message });
    }

    if (res.assessment_question) {
      setAssessmentQ(res.assessment_question);
    } else {
      setAssessmentQ(null);
    }

    if (res.assessment_complete || res.state === "PROFILE_READY") {
      setTimeout(() => {
        completeOnboarding().then(() => {
          refreshUser().then(() => navigate("/"));
        });
      }, 2000);
    }
  }

  // Fetch status on load
  useEffect(() => {
    getOnboardingStatus()
      .then((status) => {
        if (status.state === "LEARNING") {
          navigate("/");
          return;
        }
        setState(status.state);
        if (status.progress !== undefined) setProgress(status.progress);

        if (status.assessment_question) {
          setAssessmentQ(status.assessment_question);
          if (status.message) {
            setMessages([{ role: "assistant", content: status.message }]);
          }
        } else if (status.state === "ASSESSMENT") {
          // If in assessment state but no question loaded yet, request one
          sendOnboardingChat("Ready", []).then(applyResponse).catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setInitialLoading(false));
  }, [navigate]);

  async function sendMessage(textToSend?: string) {
    const text = (textToSend ?? input).trim();
    if (!text || sending) return;
    if (!textToSend) setInput("");
    appendMessage({ role: "user", content: text });
    setSending(true);
    try {
      const res = await sendOnboardingChat(
        text,
        messages.map((m) => ({ role: m.role, content: m.content })),
      );
      applyResponse(res);
    } catch {
      appendMessage({
        role: "assistant",
        content:
          "LearnAI is temporarily unavailable. Your progress is safe. Please try again.",
      });
    } finally {
      setSending(false);
    }
  }

  async function handleAssessmentSubmit() {
    if (!assessmentQ || !assessmentAnswer.trim() || submittingAnswer) return;
    setSubmittingAnswer(true);
    appendMessage({ role: "user", content: assessmentAnswer });
    const ans = assessmentAnswer;
    setAssessmentAnswer("");
    try {
      const res = await submitAssessmentAnswer(assessmentQ.attempt_id, ans);
      setAssessmentQ(null);
      applyResponse(res);
    } catch {
      appendMessage({
        role: "assistant",
        content: "Failed to submit your answer. Please try again.",
      });
    } finally {
      setSubmittingAnswer(false);
    }
  }

  const progressPercent = Math.max(progress, 5);

  return (
    <div className="onboarding-page">
      {/* Header */}
      <header className="onboarding-header">
        <div className="auth-brand" style={{ marginBottom: 0 }}>
          <div className="brand-mark">L</div>
          <span className="brand-name">LearnAI</span>
        </div>
        <div className="onboarding-phase">
          <span className="phase-label">{STATE_LABELS[state] ?? state}</span>
          <div className="phase-bar">
            <div className="phase-fill" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </header>

      {/* Main chat viewport */}
      <div className="onboarding-chat-container">
        <div className="chat-messages-list">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              {m.role === "assistant" && (
                <div className="bubble-avatar">
                  <Sparkles size={14} />
                </div>
              )}
              <div className="bubble-content">{m.content}</div>
            </div>
          ))}

          {sending && (
            <div className="chat-bubble assistant">
              <div className="bubble-avatar">
                <Sparkles size={14} />
              </div>
              <div className="bubble-content typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          {initialLoading && (
            <div className="chat-bubble assistant">
              <div className="bubble-avatar">
                <Sparkles size={14} />
              </div>
              <div className="bubble-content" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Loader2 size={16} className="spin" /> Loading your session...
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Action / Input Footer */}
        <div className="onboarding-footer">
          {assessmentQ && state === "ASSESSMENT" ? (
            <div className="assessment-answer-box">
              <div className="assessment-box-header">
                <div className="assessment-badge">
                  <HelpCircle size={14} />
                  Question {assessmentQ.index + 1} of {assessmentQ.total}
                </div>
                <span className="assessment-skill-pill">
                  {assessmentQ.skill_label} • {assessmentQ.difficulty}
                </span>
              </div>
              <textarea
                value={assessmentAnswer}
                onChange={(e) => setAssessmentAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleAssessmentSubmit();
                  }
                }}
                placeholder="Type your explanation or thoughts here... (Ctrl+Enter to submit)"
                rows={3}
                className="assessment-textarea"
                autoFocus
              />
              <div className="assessment-box-actions">
                <span className="keyboard-hint">Press <strong>Ctrl + Enter</strong> to submit</span>
                <button
                  className="primary-button submit-ans-btn"
                  onClick={handleAssessmentSubmit}
                  disabled={submittingAnswer || !assessmentAnswer.trim()}
                >
                  {submittingAnswer ? (
                    <><Loader2 size={16} className="spin" /> Evaluating...</>
                  ) : (
                    "Submit Answer →"
                  )}
                </button>
              </div>
            </div>
          ) : state === "PROFILE_READY" ? (
            <div className="onboarding-complete-banner">
              <Loader2 className="spin" size={20} />
              <span>Preparing your personalized roadmap & dashboard...</span>
            </div>
          ) : (
            <div className="chat-input-row">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                placeholder="Type your message to LearnAI..."
                disabled={sending}
                className="chat-input"
                autoFocus
              />
              <button
                className="send-button"
                onClick={() => sendMessage()}
                disabled={sending || !input.trim()}
                aria-label="Send"
              >
                {sending ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
