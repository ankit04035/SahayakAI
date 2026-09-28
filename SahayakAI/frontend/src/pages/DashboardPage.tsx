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

  const featureCards = [
    {
      title: 'Study Docs',
      description: 'Upload PDFs and notes for grounded Q&A and semantic retrieval.',
      href: '/documents',
      icon: FileText,
      accent: 'bg-blue-50 text-blue-600 border-blue-100',
    },
    {
      title: 'AI Tutor',
      description: 'Ask course questions and keep context across multi-turn chats.',
      href: '/chat',
      icon: MessageSquare,
      accent: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    },
    {
      title: 'Resume Analyzer',
      description: 'Check ATS match scores and skill gaps from your resume.',
      href: '/resumes',
      icon: Award,
      accent: 'bg-violet-50 text-violet-600 border-violet-100',
    },
    {
      title: 'Career Growth',
      description: 'Build a roadmap and track target roles with weekly milestones.',
      href: '/career/roadmap',
      icon: Compass,
      accent: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    },
  ];

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-slate-900 via-primary-900 to-indigo-800 p-6 text-white shadow-soft sm:p-8 lg:p-10">
        <div className="absolute inset-0 bg-hero-glow opacity-80" />
        <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-40 w-40 rounded-full bg-violet-400/20 blur-3xl" />

        <div className="relative z-10 grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
          <div>
            <span className="section-label border-white/20 bg-white/10 text-white">
              <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
              SahayakAI • Student Copilot
            </span>

            <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Learn faster. Get hired smarter.
            </h1>
            <p className="mt-4 max-w-xl text-sm text-slate-200 sm:text-base">
              Turn notes, lectures, and resumes into a guided career and study system powered by grounded AI, document search, and personalized progression plans.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/documents">
                <Button
                  variant="primary"
                  size="md"
                  className="bg-white text-primary-900 hover:bg-slate-100 focus:ring-white border-0 font-semibold"
                  leftIcon={<Upload className="w-4 h-4" />}
                >
                  Upload resource
                </Button>
              </Link>
              <Link to="/chat">
                <Button
                  variant="secondary"
                  size="md"
                  className="border border-white/20 bg-white/10 text-white hover:bg-white/15 focus:ring-white"
                  leftIcon={<MessageSquare className="w-4 h-4" />}
                >
                  Ask the tutor
                </Button>
              </Link>
            </div>
          </div>

          <div className="glass-panel rounded-2xl border-white/10 bg-white/10 p-5 text-left backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-300">Active Profile</p>
                <h3 className="mt-2 text-2xl font-bold text-white">User #{userId}</h3>
              </div>
              <div className="rounded-xl bg-emerald-500/20 p-2 text-emerald-300">
                <TrendingUp className="h-6 w-6" />
              </div>
            </div>

            <div className="mt-5 space-y-4 text-sm text-slate-200">
              <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2">
                <span>AI Provider</span>
                <span className="font-semibold text-white">demo</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2">
                <span>Documents</span>
                <span className="font-semibold text-white">{documents.length}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2">
                <span>Roadmap</span>
                <span className="font-semibold text-white">{latestRoadmap ? 'Live' : 'Not set'}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {featureCards.map(({ title, description, href, icon: Icon, accent }) => (
          <Link key={title} to={href} className="feature-card block h-full">
            <div className={`mb-4 inline-flex rounded-xl border p-3 ${accent}`}>
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          </Link>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Documents</span>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-600"><FileText className="h-4 w-4" /></div>
          </div>
          <div className="mt-4">
            {loading ? <Skeleton width={48} height={28} /> : <span className="text-2xl font-bold text-slate-900">{documents.length}</span>}
            <p className="mt-1 text-xs text-slate-500">Study resources indexed</p>
          </div>
        </Card>

        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Chats</span>
            <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600"><MessageSquare className="h-4 w-4" /></div>
          </div>
          <div className="mt-4">
            {loading ? <Skeleton width={48} height={28} /> : <span className="text-2xl font-bold text-slate-900">{chatSessions.length}</span>}
            <p className="mt-1 text-xs text-slate-500">Sessions in progress</p>
          </div>
        </Card>

        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Resumes</span>
            <div className="rounded-lg bg-violet-50 p-2 text-violet-600"><Award className="h-4 w-4" /></div>
          </div>
          <div className="mt-4">
            {loading ? <Skeleton width={48} height={28} /> : <span className="text-2xl font-bold text-slate-900">{resumes.length}</span>}
            <p className="mt-1 text-xs text-slate-500">ATS evaluations saved</p>
          </div>
        </Card>

        <Card padding="sm" hoverEffect>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Target role</span>
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600"><Compass className="h-4 w-4" /></div>
          </div>
          <div className="mt-4">
            {loading ? <Skeleton width={80} height={28} /> : <span className="block text-sm font-bold text-slate-900">{profile?.target_role || 'Not set'}</span>}
            <p className="mt-1 text-xs text-slate-500">{latestRoadmap ? '12-week plan active' : 'No roadmap created yet'}</p>
          </div>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Card
          title="Recent study resources"
          subtitle="Your latest documents and processing activity"
          action={<Link to="/documents" className="text-xs font-semibold text-primary-600">View all</Link>}
        >
          {loading ? (
            <div className="space-y-3">
              <Skeleton height={46} />
              <Skeleton height={46} />
              <Skeleton height={46} />
            </div>
          ) : documents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-10 text-center">
              <BookOpen className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-4 text-sm font-medium text-slate-700">No uploaded resources yet</p>
              <p className="mt-1 text-xs text-slate-500">Upload a PDF or TXT file to create a grounded learning workspace.</p>
              <Link to="/documents" className="mt-4 inline-block">
                <Button size="sm" variant="outline" leftIcon={<Upload className="w-3.5 h-3.5" />}>Upload document</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.slice(0, 4).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-slate-50 p-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-primary-600 shadow-sm ring-1 ring-slate-200">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <Link to={`/documents/${doc.id}`} className="block truncate text-sm font-semibold text-slate-900 hover:text-primary-600">
                        {doc.title || doc.original_filename || doc.filename}
                      </Link>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                        <span>{doc.file_type.toUpperCase()}</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={doc.processing_status === 'PROCESSED' ? 'success' : 'neutral'} size="sm">
                      {doc.processing_status}
                    </Badge>
                    <Link to={`/documents/${doc.id}`}>
                      <Button size="sm" variant="ghost" className="text-xs">Open</Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          title="Quick actions"
          subtitle="Jump directly into the main workflows"
        >
          <div className="space-y-3">
            <Link to="/chat" className="block rounded-2xl border border-indigo-100 bg-indigo-50 p-3 text-sm font-medium text-indigo-700 hover:bg-indigo-100">
              Start a new study chat
            </Link>
            <Link to="/resumes" className="block rounded-2xl border border-violet-100 bg-violet-50 p-3 text-sm font-medium text-violet-700 hover:bg-violet-100">
              Review resume ATS score
            </Link>
            <Link to="/career/profile" className="block rounded-2xl border border-emerald-100 bg-emerald-50 p-3 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
              Update career profile
            </Link>
            <Link to="/career/roadmap" className="block rounded-2xl border border-sky-100 bg-sky-50 p-3 text-sm font-medium text-sky-700 hover:bg-sky-100">
              Open growth roadmap
            </Link>
          </div>
        </Card>
      </section>
    </div>
  );
};
