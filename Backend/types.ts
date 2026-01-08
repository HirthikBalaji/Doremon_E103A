export interface User {
  id: string;
  name: string;
  role: string;
  avatarUrl?: string;
}

export interface AnalysisSummary {
  difficulty_rationale: string;
  kudos_evidence: string[];
  penalty_evidence: string[];
}

export interface Variables {
  base_points: number;
  difficulty_factor: number;
  peer_kudos_count: number;
  blocker_penalty_total: number;
}

// New Advanced Types for Bonus Features
export interface SkillMetric {
  name: string;
  score: number; // 0-100
  gap: number; // Negative means gap
}

export interface ProjectContribution {
  name: string;
  impact_value: string;
  role: string;
  contribution_pct: number;
}

export interface WellnessMetrics {
  burnout_risk: number; // 0-100
  async_efficiency: number; // 0-10
  timezone_load_balance: string;
  last_break_taken: string;
}

export interface CareerGrowth {
  mentorship_score: number;
  learning_velocity: number;
  promotion_readiness: number; // 0-100
  next_level_skills: string[];
}

export interface AdvancedMetrics {
  skills: SkillMetric[];
  projects: ProjectContribution[];
  wellness: WellnessMetrics;
  growth: CareerGrowth;
  innovation_score: number;
  tech_debt_reduction: number;
  customer_impact: number;
  attrition_risk_prediction: string; // Low, Medium, High
  score_history: { month: string; score: number }[]; // Trend analysis
}

export interface ScoreResponse {
  analysis_summary: AnalysisSummary;
  variables: Variables;
  final_score?: number; 
}

export interface FullUserPerformance extends User, ScoreResponse {
  final_score: number;
  advanced?: AdvancedMetrics; // Optional extended data
}