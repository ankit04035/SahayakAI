import { apiRequest } from './client';
import { CareerProfileRead, RoadmapRead } from '../types/career';

export async function getCareerProfile(userId?: number): Promise<CareerProfileRead> {
  return apiRequest<CareerProfileRead>('/career/profile', { userId });
}

export async function upsertCareerProfile(
  profile: {
    target_role: string;
    degree?: string;
    current_skills?: string[];
    experience?: string;
    interests?: string[];
  },
  userId?: number
): Promise<CareerProfileRead> {
  return apiRequest<CareerProfileRead>('/career/profile', {
    method: 'POST',
    body: JSON.stringify(profile),
    userId,
  });
}

export async function deleteCareerProfile(userId?: number): Promise<{ message: string }> {
  return apiRequest<{ message: string }>('/career/profile', {
    method: 'DELETE',
    userId,
  });
}

export async function generateRoadmap(
  params: {
    target_role?: string;
    resume_id?: number;
    custom_interests?: string[];
  },
  userId?: number
): Promise<RoadmapRead> {
  return apiRequest<RoadmapRead>('/career/roadmaps/generate', {
    method: 'POST',
    body: JSON.stringify(params),
    userId,
  });
}

export async function listRoadmaps(userId?: number): Promise<RoadmapRead[]> {
  return apiRequest<RoadmapRead[]>('/career/roadmaps', { userId });
}

export async function getRoadmap(roadmapId: number, userId?: number): Promise<RoadmapRead> {
  return apiRequest<RoadmapRead>(`/career/roadmaps/${roadmapId}`, { userId });
}

export async function deleteRoadmap(roadmapId: number, userId?: number): Promise<{ message: string; id: number }> {
  return apiRequest<{ message: string; id: number }>(`/career/roadmaps/${roadmapId}`, {
    method: 'DELETE',
    userId,
  });
}
