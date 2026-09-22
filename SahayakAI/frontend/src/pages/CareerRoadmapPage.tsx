import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  Sparkles,
  Calendar,
  CheckCircle2,
  Layers,
  Award,
  ArrowRight,
  BookOpen,
  FolderGit2,
  Trash2,
  Clock,
  Target,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { generateRoadmap, listRoadmaps, getRoadmap, deleteRoadmap, getCareerProfile } from '../api/career';
import { listResumes } from '../api/resumes';
import { RoadmapRead, CareerProfileRead, WeeklyPlanItem as MilestoneRead } from '../types/career';
import { ResumeRead } from '../types/resume';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { formatDate } from '../utils/formatters';

export const CareerRoadmapPage: React.FC = () => {
  const { userId } = useUser();
  const [roadmaps, setRoadmaps] = useState<RoadmapRead[]>([]);
  const [selectedRoadmap, setSelectedRoadmap] = useState<RoadmapRead | null>(null);
  const [profile, setProfile] = useState<CareerProfileRead | null>(null);
  const [resumes, setResumes] = useState<ResumeRead[]>([]);
  const [loading, setLoading] = useState(true);

  // Generate modal
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [targetRoleInput, setTargetRoleInput] = useState('');
  const [selectedResumeId, setSelectedResumeId] = useState<number | undefined>(undefined);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const fetchRoadmapsData = async () => {
    setLoading(true);
    try {
      const [roadmapsData, profileData, resumesData] = await Promise.allSettled([
        listRoadmaps(userId),
        getCareerProfile(userId),
        listResumes(userId),
      ]);

      if (roadmapsData.status === 'fulfilled') {
        setRoadmaps(roadmapsData.value);
        if (roadmapsData.value.length > 0 && !selectedRoadmap) {
          setSelectedRoadmap(roadmapsData.value[0]);
        }
      }

      if (profileData.status === 'fulfilled') {
        setProfile(profileData.value);
        if (!targetRoleInput) setTargetRoleInput(profileData.value.target_role || '');
      }

      if (resumesData.status === 'fulfilled') {
        setResumes(resumesData.value);
      }
    } catch (err) {
      console.error('Failed to load roadmap data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoadmapsData();
  }, [userId]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenerateError(null);
    try {
      const result = await generateRoadmap(
        {
          target_role: targetRoleInput.trim() || undefined,
          resume_id: selectedResumeId,
        },
        userId
      );
      setRoadmaps((prev) => [result, ...prev]);
      setSelectedRoadmap(result);
      setIsGenerateModalOpen(false);
    } catch (err: any) {
      setGenerateError(err.message || 'Failed to generate roadmap');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteRoadmap = async (roadmapId: number) => {
    if (!confirm('Are you sure you want to delete this career roadmap?')) return;
    try {
      await deleteRoadmap(roadmapId, userId);
      const remaining = roadmaps.filter((r) => r.id !== roadmapId);
      setRoadmaps(remaining);
      if (selectedRoadmap?.id === roadmapId) {
        setSelectedRoadmap(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Career Roadmaps</h1>
          <p className="text-sm text-gray-500 mt-1">
            Personalized 12-week progression schedules across 6 bi-weekly phases with curated project deliverables.
          </p>
        </div>
        <Button
          onClick={() => {
            setGenerateError(null);
            setIsGenerateModalOpen(true);
          }}
          leftIcon={<Sparkles className="w-4 h-4" />}
        >
          Generate New Roadmap
        </Button>
      </div>

      {loading ? (
        <div className="py-20 text-center">
          <LoadingSpinner size="lg" label="Loading career roadmaps..." />
        </div>
      ) : roadmaps.length === 0 ? (
        <EmptyState
          icon={<Compass className="w-8 h-8 text-primary-500" />}
          title="No Career Roadmaps Generated"
          description="Create your personalized 12-week roadmap tailored to your target discipline, current skill gaps, and resume profile."
          action={
            <Button size="sm" onClick={() => setIsGenerateModalOpen(true)} leftIcon={<Sparkles className="w-4 h-4" />}>
              Generate 12-Week Roadmap
            </Button>
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Roadmap Selector Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {roadmaps.map((r) => {
              const isSelected = selectedRoadmap?.id === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedRoadmap(r)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition border ${
                    isSelected
                      ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                      : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>{(r.target_role || r.title)}</span>
                  <span className={`text-2xs px-1.5 py-0.5 rounded-full ${isSelected ? 'bg-primary-700' : 'bg-gray-100'}`}>
                    #{r.id}
                  </span>
                </button>
              );
            })}
          </div>

          {selectedRoadmap && (
            <div className="space-y-6">
              {/* Selected Roadmap Header Card */}
              <Card>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="purple" size="sm">12-Week Progression</Badge>
                      <span className="text-2xs text-gray-400">Created {formatDate(selectedRoadmap.created_at)}</span>
                    </div>
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                      {(selectedRoadmap.target_role || selectedRoadmap.title)}
                    </h2>
                    {(selectedRoadmap.rationale || (selectedRoadmap.recommendation_reasons && selectedRoadmap.recommendation_reasons.join(', '))) && (
                      <p className="text-xs text-gray-600 mt-2 max-w-2xl leading-relaxed">
                        {(selectedRoadmap.rationale || (selectedRoadmap.recommendation_reasons && selectedRoadmap.recommendation_reasons.join(', ')))}
                      </p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteRoadmap(selectedRoadmap.id)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 self-start sm:self-auto"
                    leftIcon={<Trash2 className="w-4 h-4" />}
                  >
                    Delete Roadmap
                  </Button>
                </div>
              </Card>

              {/* 12-Week Timeline (6 Bi-Weekly Phases) */}
              <div className="space-y-4">
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-primary-600" />
                  12-Week Milestone Progression
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {((selectedRoadmap.weekly_plan || selectedRoadmap.milestones) || []).map((milestone: MilestoneRead, idx: number) => (
                    <div
                      key={idx}
                      className="bg-white rounded-xl border border-gray-200 p-5 shadow-2xs hover:border-primary-300 transition flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-2xs font-bold text-primary-700 bg-primary-50 px-2 py-0.5 rounded-full border border-primary-200 uppercase tracking-wider">
                            {milestone.week_range || `Phase ${idx + 1}`}
                          </span>
                          <span className="text-2xs text-gray-400 font-semibold">Phase {idx + 1} of 6</span>
                        </div>

                        <h4 className="text-sm font-bold text-gray-900 mb-1.5">{milestone.title}</h4>
                        <p className="text-xs text-gray-600 leading-relaxed mb-3">
                          {milestone.description}
                        </p>

                        {/* Skills focus */}
                        {milestone.skills && milestone.skills.length > 0 && (
                          <div className="mb-3">
                            <span className="text-2xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">
                              Target Competencies:
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {milestone.skills.map((s: string, si: number) => (
                                <Badge key={si} variant="neutral" size="sm">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Project Deliverable */}
                      {milestone.recommended_project && (
                        <div className="mt-3 pt-3 border-t border-gray-100 bg-gray-50/70 -mx-5 -mb-5 p-4 rounded-b-xl">
                          <span className="text-2xs font-bold text-indigo-700 uppercase tracking-wider block mb-1 flex items-center gap-1">
                            <FolderGit2 className="w-3 h-3" />
                            Milestone Project
                          </span>
                          <p className="text-xs text-gray-800 font-medium">{milestone.recommended_project}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Projects & Technical Interview Topics */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recommended Projects */}
                {(selectedRoadmap.projects || selectedRoadmap.recommended_projects || []).length > 0 && (
                  <Card
                    title={
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-primary-600" />
                        <span>Recommended Capstone Projects</span>
                      </div>
                    }
                    subtitle="Portfolio-worthy implementations to showcase in interviews"
                  >
                    <div className="space-y-3">
                      {(selectedRoadmap.projects || selectedRoadmap.recommended_projects || []).map((proj: any, pi: number) => {
                        const title = typeof proj === 'string' ? proj : proj.title || proj.name;
                        const desc = typeof proj === 'object' ? proj.description || proj.deliverable : null;
                        return (
                          <div key={pi} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                            <h5 className="text-xs font-bold text-gray-900">{title}</h5>
                            {desc && <p className="text-2xs text-gray-600 mt-1">{desc}</p>}
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                )}

                {/* Technical Interview Topics */}
                {selectedRoadmap.interview_topics && selectedRoadmap.interview_topics.length > 0 && (
                  <Card
                    title={
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-primary-600" />
                        <span>Technical Interview Topics</span>
                      </div>
                    }
                    subtitle="Core competencies and question categories to prepare"
                  >
                    <div className="space-y-2">
                      {selectedRoadmap.interview_topics.map((topic: any, ti: number) => {
                        const title = typeof topic === 'string' ? topic : topic.topic || topic.name;
                        return (
                          <div key={ti} className="flex items-center gap-2 text-xs text-gray-700 bg-white p-2.5 rounded border border-gray-100 shadow-2xs">
                            <CheckCircle2 className="w-3.5 h-3.5 text-primary-600 shrink-0" />
                            <span>{title}</span>
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generate Roadmap Modal */}
      <Modal
        isOpen={isGenerateModalOpen}
        onClose={() => !generating && setIsGenerateModalOpen(false)}
        title="Generate 12-Week Roadmap"
        description="SahayakAI will synthesize your target role and resume profile into 6 bi-weekly phases."
        maxWidth="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsGenerateModalOpen(false)} disabled={generating}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleGenerate} isLoading={generating}>
              Generate Roadmap
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {generateError && <Alert type="error" message={generateError} />}

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Target Role / Discipline
            </label>
            <input
              type="text"
              placeholder="e.g. Software Engineer, Machine Learning Engineer"
              value={targetRoleInput}
              onChange={(e) => setTargetRoleInput(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {profile?.target_role && (
              <p className="text-2xs text-gray-400 mt-1">
                Profile default: <span className="font-semibold text-gray-600">{profile.target_role}</span>
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Link Resume (Optional - to target skill gaps)
            </label>
            <select
              value={selectedResumeId ?? ''}
              onChange={(e) => setSelectedResumeId(e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">No Resume (Use standard role progression)</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  Resume #{r.id}: {(r.original_filename || r.filename)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Modal>
    </div>
  );
};
