export interface CareerProfileRead {
  id: number;
  user_id: number;
  degree?: string | null;
  target_role: string;
  current_skills?: string[] | null;
  experience?: string | null;
  interests?: string[] | null;
  created_at: string;
  updated_at?: string | null;
}

export interface WeeklyPlanItem {
  week_range: string;
  focus: string;
  learning_goals: string[];
  deliverable: string;
  title?: string;
  description?: string;
  skills?: string[];
  recommended_project?: string;
}

export type MilestoneRead = WeeklyPlanItem;

export interface ProjectRecommendation {
  title: string;
  skills: string[];
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | string;
  description: string;
}

export interface RoadmapRead {
  id: number;
  career_profile_id: number;
  title: string;
  target_role?: string;
  rationale?: string;
  recommended_skills?: string[];
  missing_skills?: string[];
  projects?: ProjectRecommendation[];
  recommended_projects?: any[];
  learning_order?: string[];
  weekly_plan?: WeeklyPlanItem[];
  milestones?: MilestoneRead[];
  interview_topics?: string[] | any[];
  recommendation_reasons?: string[];
  created_at: string;
  updated_at?: string | null;
}
