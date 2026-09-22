import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  Award,
  Compass,
  Upload,
  ArrowRight,
  TrendingUp,
  Clock,
  Sparkles,
  BookOpen,
  CheckCircle2,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getDocuments } from '../api/documents';
import { listChatSessions } from '../api/chat';
import { listResumes } from '../api/resumes';
import { getCareerProfile, listRoadmaps } from '../api/career';
import { DocumentRead } from '../types/document';
import { ChatSessionRead } from '../types/chat';
import { ResumeRead } from '../types/resume';
import { CareerProfileRead, RoadmapRead } from '../types/career';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Skeleton } from '../components/common/Skeleton';
import { formatDate, formatFileSize } from '../utils/formatters';

export const DashboardPage: React.FC = () => {
  const { userId } = useUser();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSessionRead[]>([]);
  const [resumes, setResumes] = useState<ResumeRead[]>([]);
  const [profile, setProfile] = useState<CareerProfileRead | null>(null);
  const [roadmaps, setRoadmaps] = useState<RoadmapRead[]>([]);

  useEffect(() => {
    let isMounted = true;
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        const [docsRes, chatsRes, resumesRes, roadmapsRes] = await Promise.allSettled([
          getDocuments(userId, 0, 5),
          listChatSessions(userId),
          listResumes(userId),
          listRoadmaps(userId),
        ]);

        if (!isMounted) return;

        if (docsRes.status === 'fulfilled') setDocuments(docsRes.value);
        if (chatsRes.status === 'fulfilled') setChatSessions(chatsRes.value);
        if (resumesRes.status === 'fulfilled') setResumes(resumesRes.value);
        if (roadmapsRes.status === 'fulfilled') setRoadmaps(roadmapsRes.value);

        try {
          const profRes = await getCareerProfile(userId);
          if (isMounted) setProfile(profRes);
        } catch {
          if (isMounted) setProfile(null);
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, [userId]);

  const latestRoadmap = roadmaps.length > 0 ? roadmaps[0] : null;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-primary-900 via-primary-800 to-indigo-900 rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-10 -translate-y-10 w-64 h-64 bg-primary-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-xs text-primary-200 text-xs font-medium mb-3">
            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            Active Session: Dev User #{userId}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">
            Welcome to SahayakAI
          </h1>
          <p className="text-primary-100 text-sm sm:text-base leading-relaxed mb-6">
            Your unified AI-powered assistant for academic document RAG, intelligent study chats, resume ATS optimization, and 12-week personalized career progression.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Link to="/documents">
              <Button
                variant="primary"
                size="sm"
                className="bg-white text-primary-900 hover:bg-primary-50 focus:ring-white border-0 font-semibold"
                leftIcon={<Upload className="w-4 h-4 text-primary-700" />}
              >
                Upload Document
              </Button>
            </Link>
            <Link to="/chat">
              <Button
                variant="secondary"
                size="sm"
                className="bg-primary-800/80 text-white border-primary-600 hover:bg-primary-700/80"
                leftIcon={<MessageSquare className="w-4 h-4" />}
              >
                Start Study Chat
              </Button>
            </Link>
            <Link to="/career/roadmap">
              <Button
                variant="ghost"
                size="sm"
                className="text-primary-100 hover:bg-white/10 hover:text-white"
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                View Roadmap
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Documents</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton width={48} height={28} />
            ) : (
              <span className="text-2xl font-bold text-gray-900">{documents.length}</span>
            )}
            <p className="text-xs text-gray-500 mt-1">Processed study materials</p>
          </div>
        </Card>

        {/* Metric 2 */}
        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Chat Sessions</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton width={48} height={28} />
            ) : (
              <span className="text-2xl font-bold text-gray-900">{chatSessions.length}</span>
            )}
            <p className="text-xs text-gray-500 mt-1">Active study conversations</p>
          </div>
        </Card>

        {/* Metric 3 */}
        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Resumes</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton width={48} height={28} />
            ) : (
              <span className="text-2xl font-bold text-gray-900">{resumes.length}</span>
            )}
            <p className="text-xs text-gray-500 mt-1">Uploaded for ATS analysis</p>
          </div>
        </Card>

        {/* Metric 4 */}
        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Career Track</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Compass className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton width={80} height={28} />
            ) : (
              <span className="text-sm font-bold text-gray-900 truncate block">
                {profile?.target_role || 'Not Set'}
              </span>
            )}
            <p className="text-xs text-gray-500 mt-1">
              {latestRoadmap ? '12-Week Roadmap Active' : 'No Roadmap Created'}
            </p>
          </div>
        </Card>
      </div>

      {/* Main Grid: Recent Documents & Recent Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents */}
        <div className="lg:col-span-2 space-y-4">
          <Card
            title="Recent Study Documents"
            subtitle="Uploaded lecture notes, textbooks, and research papers"
            action={
              <Link to="/documents" className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {loading ? (
              <div className="space-y-3">
                <Skeleton height={50} />
                <Skeleton height={50} />
                <Skeleton height={50} />
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-600">No documents uploaded yet</p>
                <p className="text-xs text-gray-400 mt-1 mb-4">Upload a PDF or TXT document to begin RAG query grounding.</p>
                <Link to="/documents">
                  <Button size="sm" variant="outline" leftIcon={<Upload className="w-3.5 h-3.5" />}>
                    Upload First Document
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {documents.slice(0, 4).map((doc) => (
                  <div key={doc.id} className="py-3 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4 text-primary-600" />
                      </div>
                      <div className="min-w-0">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="text-sm font-medium text-gray-900 hover:text-primary-600 truncate block transition"
                        >
                          {doc.title || doc.original_filename || doc.filename}
                        </Link>
                        <div className="flex items-center gap-2 text-2xs text-gray-400 mt-0.5">
                          <span>{doc.file_type.toUpperCase()}</span>
                          <span>•</span>
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>•</span>
                          <span>{formatDate(doc.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={doc.processing_status === 'PROCESSED' ? 'success' : 'neutral'} size="sm">
                        {doc.processing_status}
                      </Badge>
                      <Link to={`/documents/${doc.id}`}>
                        <Button size="sm" variant="ghost" className="text-xs">
                          Inspect
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Active Roadmap Preview */}
          {latestRoadmap && (
            <Card
              title="Active Career Roadmap"
              subtitle={`12-Week progression toward ${(latestRoadmap.target_role || latestRoadmap.title)}`}
              action={
                <Link to="/career/roadmap" className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
                  Full Roadmap <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              }
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-700">Progression Milestones:</span>
                  <Badge variant="purple" size="sm">{(latestRoadmap.weekly_plan || latestRoadmap.milestones)?.length || 6} Bi-Weekly Phases</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {((latestRoadmap.weekly_plan || latestRoadmap.milestones) || []).slice(0, 3).map((m, idx) => (
                    <div key={idx} className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                      <span className="text-2xs font-bold text-primary-600 uppercase tracking-wider block mb-1">
                        {m.week_range || `Phase ${idx + 1}`}
                      </span>
                      <h4 className="text-xs font-semibold text-gray-900 truncate">{(m.title || m.focus)}</h4>
                      <p className="text-2xs text-gray-500 line-clamp-2 mt-1">{(m.description || m.deliverable)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Chat Sessions & Quick Tips */}
        <div className="space-y-6">
          <Card
            title="Study Assistant Chats"
            subtitle="Recent multi-turn conversations"
            action={
              <Link to="/chat" className="text-xs font-semibold text-primary-600 hover:text-primary-700">
                Open Chat
              </Link>
            }
          >
            {loading ? (
              <div className="space-y-3">
                <Skeleton height={40} />
                <Skeleton height={40} />
              </div>
            ) : chatSessions.length === 0 ? (
              <div className="text-center py-6">
                <MessageSquare className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-xs text-gray-500">No active chat sessions.</p>
                <Link to="/chat">
                  <Button size="sm" variant="outline" className="mt-3 text-xs">
                    New Chat
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {chatSessions.slice(0, 4).map((session) => (
                  <Link
                    key={session.id}
                    to="/chat"
                    state={{ activeSessionId: session.id }}
                    className="block p-3 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-semibold text-gray-800 truncate group-hover:text-primary-700">
                        {session.title || `Chat #${session.id}`}
                      </h4>
                      <span className="text-2xs text-gray-400 shrink-0">
                        {formatDate(session.created_at)}
                      </span>
                    </div>
                    {session.document_id && (
                      <div className="mt-1.5 flex items-center gap-1 text-2xs text-primary-600 font-medium">
                        <FileText className="w-3 h-3" />
                        <span>Document Grounded (Doc #{session.document_id})</span>
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* Quick Info Card */}
          <div className="bg-gradient-to-br from-indigo-50 to-primary-50 border border-primary-100 rounded-xl p-5">
            <div className="flex items-center gap-2 text-primary-800 font-semibold text-sm mb-2">
              <CheckCircle2 className="w-4 h-4 text-primary-600" />
              <span>Enterprise Guardrails</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">
              All questions asked through Study Assistant are filtered through vector similarity gating. If reference material has insufficient evidence, the assistant clearly informs you instead of hallucinating.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
