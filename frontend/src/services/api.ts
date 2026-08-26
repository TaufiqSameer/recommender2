import type {
    ActivityHistoryItem,
    ActivitySubmission,
    LearnerStateResponse,
    NextActivityResponse,
    SubmitActivityResponse,
  } from "../types/learning";
  
  
  const API_BASE_URL = "http://127.0.0.1:8000";
  
  
  async function request<T>(
    endpoint: string,
    options?: RequestInit,
  ): Promise<T> {
  
    const response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        headers: {
          "Content-Type": "application/json",
          ...(options?.headers ?? {}),
        },
  
        ...options,
      },
    );
  
  
    if (!response.ok) {
  
      let message =
        `API request failed: ${response.status}`;
  
      try {
  
        const error = await response.json();
  
        if (error.detail) {
          message = error.detail;
        }
  
      } catch {
        // Keep the default error message.
      }
  
      throw new Error(message);
    }
  
  
    return response.json();
  }
  
  
  export async function getLearnerState(
    learnerId: string,
  ): Promise<LearnerStateResponse> {
  
    return request<LearnerStateResponse>(
      `/api/learners/${learnerId}/state`,
    );
  }
  
  
  export async function getNextActivity(
    learnerId: string,
  ): Promise<NextActivityResponse> {
  
    return request<NextActivityResponse>(
      `/api/learners/${learnerId}/next-activity`,
    );
  }
  
  
  export async function getActivityHistory(
    learnerId: string,
  ): Promise<ActivityHistoryItem[]> {
  
    return request<ActivityHistoryItem[]>(
      `/api/learners/${learnerId}/activities`,
    );
  }
  
  
  export async function submitActivity(
    learnerId: string,
    activityId: string,
    submission: ActivitySubmission,
  ): Promise<SubmitActivityResponse> {
  
    return request<SubmitActivityResponse>(
      `/api/learners/${learnerId}/activities/${activityId}/submit`,
      {
        method: "POST",
  
        body: JSON.stringify(submission),
      },
    );
  }