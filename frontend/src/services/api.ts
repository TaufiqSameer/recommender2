import type {
  ActivityHistoryResponse,
  LearnerStateResponse,
  NextActivityResponse,
  SubmitActivityResponse,
} from "../types/learning";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

// ─── Token helpers ───────────────────────────────────────────────────────────

export function getToken(): string | null {
  return localStorage.getItem("eurekaai_token") || localStorage.getItem("learnai_token");
}

export function setToken(token: string): void {
  localStorage.setItem("eurekaai_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("eurekaai_token");
  localStorage.removeItem("learnai_token");
}

// ─── Core request ────────────────────────────────────────────────────────────

async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> ?? {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `API request failed: ${response.status}`;
    try {
      const error = await response.json();
      if (error.detail) message = error.detail;
    } catch {
      // keep default
    }
    throw new Error(message);
  }

  return response.json();
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export type AuthResponse = {
  access_token: string;
  token_type: string;
  learner_id: string;
  username: string;
  display_name: string | null;
};

export type MeResponse = {
  user_id: string;
  email: string;
  username: string;
  learner_id: string;
  display_name: string | null;
  onboarding_state: string;
  goal?: string | null;
  target_role?: string | null;
  domain?: string | null;
  weekly_hours?: number | null;
  learning_preferences?: string[] | null;
  preferences?: Record<string, any> | null;
};

export type UpdateProfilePayload = {
  display_name?: string;
  goal?: string;
  target_role?: string;
  domain?: string;
  weekly_hours?: number;
  learning_preferences?: string[];
  preferences?: Record<string, any>;
};

export async function signup(
  email: string,
  username: string,
  password: string,
  displayName?: string,
): Promise<AuthResponse> {
  return request<AuthResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, username, password, display_name: displayName }),
  });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<MeResponse> {
  return request<MeResponse>("/api/auth/me");
}

export async function updateMe(data: UpdateProfilePayload): Promise<MeResponse> {
  return request<MeResponse>("/api/auth/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ─── Onboarding ──────────────────────────────────────────────────────────────

export type OnboardingStatusResponse = {
  state: string;
  learner_id: string;
  goal: string | null;
  domain: string | null;
  display_name: string | null;
  progress?: number;
  assessment_question?: AssessmentQuestion | null;
  assessment_complete?: boolean;
  message?: string | null;
};

export type OnboardingChatResponse = {
  message: string;
  state: string;
  progress: number;
  assessment_question: AssessmentQuestion | null;
  assessment_complete: boolean;
};

export type AssessmentQuestion = {
  index: number;
  total: number;
  attempt_id: string;
  skill_id: string;
  skill_label: string;
  question: string;
  question_type: string;
  difficulty: string;
};

export async function getOnboardingStatus(): Promise<OnboardingStatusResponse> {
  return request<OnboardingStatusResponse>("/api/onboarding/status");
}

export async function sendOnboardingChat(
  message: string,
  history: ChatMessage[],
): Promise<OnboardingChatResponse> {
  return request<OnboardingChatResponse>("/api/onboarding/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
}

export async function submitAssessmentAnswer(
  attemptId: string,
  answer: string,
): Promise<OnboardingChatResponse> {
  return request<OnboardingChatResponse>("/api/onboarding/assessment/answer", {
    method: "POST",
    body: JSON.stringify({ attempt_id: attemptId, answer }),
  });
}

export async function completeOnboarding(): Promise<void> {
  await request("/api/onboarding/complete", { method: "POST" });
}

// ─── Learner / Learning ──────────────────────────────────────────────────────

export async function getLearnerState(
  learnerId: string,
): Promise<LearnerStateResponse> {
  return request<LearnerStateResponse>(`/api/learners/${learnerId}/state`);
}

export async function getNextActivity(
  learnerId: string,
): Promise<NextActivityResponse> {
  return request<NextActivityResponse>(`/api/learners/${learnerId}/next-activity`);
}

export async function getActivityHistory(
  learnerId: string,
): Promise<ActivityHistoryResponse> {
  return request<ActivityHistoryResponse>(`/api/learners/${learnerId}/activities`);
}

export async function submitActivity(
  learnerId: string,
  activityId: string,
  answer: string,
): Promise<SubmitActivityResponse> {
  return request<SubmitActivityResponse>(
    `/api/learners/${learnerId}/activities/${activityId}/submit`,
    {
      method: "POST",
      body: JSON.stringify({ answer }),
    },
  );
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LearningChatResponse = {
  message: string;
  context: {
    skill_id: string | null;
    mastery: number | null;
    confidence: number | null;
  };
};

export async function sendLearningChat(
  learnerId: string,
  message: string,
  activityId?: string,
  conversationHistory: ChatMessage[] = [],
): Promise<LearningChatResponse> {
  return request<LearningChatResponse>(`/api/learners/${learnerId}/chat`, {
    method: "POST",
    body: JSON.stringify({
      message,
      activity_id: activityId ?? null,
      conversation_history: conversationHistory,
    }),
  });
}

// Chat sessions

export type ChatSessionSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatSessionDetail = {
  id: string;
  title: string;
  messages: {
    id: string;
    role: string;
    content: string;
    created_at: string;
  }[];
};

export async function createChatSession(title?: string): Promise<{ id: string; title: string }> {
  return request("/api/chat/sessions", {
    method: "POST",
    body: JSON.stringify({ title: title ?? "New conversation" }),
  });
}

export async function getChatSessions(): Promise<{ sessions: ChatSessionSummary[] }> {
  return request("/api/chat/sessions");
}

export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
  return request(`/api/chat/sessions/${sessionId}`);
}

export async function sendChatSessionMessage(
  sessionId: string,
  content: string,
  activityId?: string,
): Promise<{
  user_message: { id: string; role: string; content: string };
  assistant_message: { id: string; role: string; content: string };
}> {
  return request(`/api/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content, activity_id: activityId ?? null }),
  });
}

// ─── Progress ────────────────────────────────────────────────────────────────

export type ProgressResponse = {
  overall_mastery: number;
  skills_mastered: number;
  skills_learning: number;
  activities_completed: number;
  streak_days: number;
  skill_mastery: {
    skill_id: string;
    label: string;
    mastery: number;
    status: string;
    attempts: number;
  }[];
  evidence_timeline: {
    date: string;
    score: number;
    skill_id: string;
  }[];
};

export async function getProgress(): Promise<ProgressResponse> {
  return request<ProgressResponse>("/api/progress");
}

// ─── Graph ───────────────────────────────────────────────────────────────────

export type GraphResponse = {
  nodes: {
    id: string;
    label: string;
    domain: string;
    difficulty: number;
    mastery: number;
    status: string;
    attempts: number;
  }[];
  edges: {
    source: string;
    target: string;
  }[];
  domain: string | null;
};

export async function getSkillGraph(): Promise<GraphResponse> {
  return request<GraphResponse>("/api/graph");
}