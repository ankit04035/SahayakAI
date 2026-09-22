import { apiRequest } from './client';
import { ResumeRead, ResumeAnalysisRead } from '../types/resume';

export async function uploadResume(file: File, userId?: number): Promise<ResumeRead> {
  const formData = new FormData();
  formData.append('file', file);
  if (userId) formData.append('user_id', String(userId));

  return apiRequest<ResumeRead>('/resumes', {
    method: 'POST',
    body: formData,
    userId,
  });
}

export async function listResumes(userId?: number): Promise<ResumeRead[]> {
  return apiRequest<ResumeRead[]>('/resumes', { userId });
}

export async function getResume(resumeId: number, userId?: number): Promise<ResumeRead> {
  return apiRequest<ResumeRead>(`/resumes/${resumeId}`, { userId });
}

export async function deleteResume(resumeId: number, userId?: number): Promise<{ message: string; id: number }> {
  return apiRequest<{ message: string; id: number }>(`/resumes/${resumeId}`, {
    method: 'DELETE',
    userId,
  });
}

export async function analyzeResume(
  resumeId: number,
  jobDescription?: string,
  userId?: number
): Promise<ResumeAnalysisRead> {
  const body = jobDescription ? JSON.stringify({ job_description: jobDescription }) : JSON.stringify({});
  return apiRequest<ResumeAnalysisRead>(`/resumes/${resumeId}/analyze`, {
    method: 'POST',
    body,
    userId,
  });
}

export async function listResumeAnalyses(resumeId: number, userId?: number): Promise<ResumeAnalysisRead[]> {
  return apiRequest<ResumeAnalysisRead[]>(`/resumes/${resumeId}/analyses`, { userId });
}

export async function getResumeAnalysis(
  resumeId: number,
  analysisId: number,
  userId?: number
): Promise<ResumeAnalysisRead> {
  return apiRequest<ResumeAnalysisRead>(`/resumes/${resumeId}/analyses/${analysisId}`, { userId });
}
