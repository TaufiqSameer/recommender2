export interface LearnerSkillState {
    skill_id: string;
    mastery: number;
    theta: number;
    confidence: number;
    attempts: number;
    status: string;
    last_assessed_at: string | null;
  }
  
  
  export interface LearnerStateResponse {
    learner_id: string;
    skills: LearnerSkillState[];
  }
  
  
  export interface Skill {
    id: string;
    label: string;
  }
  
  
  export interface Recommendation {
    score: number;
    reason: string;
  }
  
  
  export interface LearningActivity {
    title: string;
    type: string;
    objective: string;
    difficulty: string;
    instructions: string;
    hints: string[];
  }
  
  
  export interface NextActivityResponse {
    activity_id: string;
    skill: Skill;
    recommendation: Recommendation;
    activity: LearningActivity;
  }
  
  
  export interface ActivitySubmission {
    answer: string;
  }
  
  
  export interface Evaluation {
    score: number;
    correct: boolean;
    feedback: string;
    strengths: string[];
    weaknesses: string[];
    next_step: string;
  }
  
  
  export interface EvaluationLearnerState {
    skill_id: string;
    mastery: number;
    theta: number;
    confidence: number;
    attempts: number;
    status: string;
  }
  
  
  export interface SubmitActivityResponse {
    activity_id: string;
    evaluation: Evaluation;
    learner_state: EvaluationLearnerState;
  }
  
  
  export interface ActivityHistoryItem {
    activity_id: string;
    skill_id: string;
    skill_label?: string;
    title: string;
    type: string;
    objective: string;
    difficulty: string;
    instructions: string;
    hints: string[];
    recommendation_score: number;
    generation_source: string;
    created_at: string;
    completed?: boolean;
    score?: number | null;
  }

  export interface ActivityHistoryResponse {
    learner_id: string;
    activities_completed: number;
    activities: ActivityHistoryItem[];
  }

  export interface SubmitActivityResponse {
    activity_id: string;
  
    evaluation: {
      score: number;
      correct: boolean;
      feedback: string;
      strengths: string[];
      weaknesses: string[];
      next_step: string;
    };
  
    learner_state: {
      skill_id: string;
      mastery: number;
      theta: number;
      confidence: number;
      attempts: number;
      status: string;
    };
  }