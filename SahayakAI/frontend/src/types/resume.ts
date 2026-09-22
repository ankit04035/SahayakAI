export interface ResumeRead {
  id: number;
  user_id: number;
  original_filename: string;
  filename?: string;
  stored_filename: string;
  file_type: string;
  file_size: number;
  processing_status: string;
  parsed_data?: {
    skills?: string[];
    education?: any[];
    experience?: any[];
    [key: string]: any;
  } | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ResumeEducation {
  degree?: string;
  institution?: string;
  year?: string;
  description?: string;
}

export interface ResumeExperience {
  role?: string;
  company?: string;
  duration?: string;
  description?: string;
}

export interface ResumeAnalysisRead {
  id: number;
  resume_id: number;
  job_description?: string | null;
  match_score?: number | null;
  score: number;
  target_role?: string;
  extracted_skills: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  recommendations?: string[];
  education_data?: ResumeEducation[];
  experience_data?: ResumeExperience[];
  created_at: string;
  updated_at?: string | null;
}
