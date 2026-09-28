import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { UserProvider } from '../context/UserContext';
import { DocumentsPage } from '../pages/DocumentsPage';
import { ChatPage } from '../pages/ChatPage';
import { ResumePage } from '../pages/ResumePage';
import { CareerProfilePage } from '../pages/CareerProfilePage';
import { CareerRoadmapPage } from '../pages/CareerRoadmapPage';
import { DashboardPage } from '../pages/DashboardPage';
import { getCareerProfile } from '../api/career';

// Mock API modules
vi.mock('../api/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue({ id: 1, name: 'Student Test', email: 'student@example.com', created_at: '2026-09-23T00:00:00Z' }),
  registerAccount: vi.fn(),
  loginAccount: vi.fn(),
  logoutAccount: vi.fn(),
}));

vi.mock('../api/documents', () => ({
  getDocuments: vi.fn().mockResolvedValue([
    {
      id: 1,
      user_id: 1,
      title: 'Operating Systems Ch 1',
      original_filename: 'os_ch1.pdf',
      file_type: 'pdf',
      file_size: 2048,
      processing_status: 'completed',
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  uploadDocument: vi.fn().mockResolvedValue({
    id: 2,
    user_id: 1,
    title: 'New Upload',
    original_filename: 'test.pdf',
    file_type: 'pdf',
    file_size: 1024,
    processing_status: 'completed',
    chunk_count: 3,
    created_at: '2026-09-23T00:00:00Z',
  }),
  deleteDocument: vi.fn().mockResolvedValue({ message: 'Deleted', id: 1 }),
}));

vi.mock('../api/chat', () => ({
  listChatSessions: vi.fn().mockResolvedValue([
    {
      id: 10,
      user_id: 1,
      title: 'OS Exam Prep',
      document_id: 1,
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  listChatMessages: vi.fn().mockResolvedValue([
    {
      id: 101,
      session_id: 10,
      role: 'user',
      content: 'Explain process states',
      created_at: '2026-09-23T00:00:00Z',
    },
    {
      id: 102,
      session_id: 10,
      role: 'assistant',
      content: 'Process states include Ready, Running, and Blocked.',
      sources: [
        {
          chunk_id: 1,
          chunk_index: 0,
          page: 1,
          page_number: 1,
          similarity: 0.88,
          similarity_score: 0.88,
          content_preview: 'A process transitions from ready to running...',
        },
      ],
      insufficient_evidence: false,
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  createChatSession: vi.fn().mockResolvedValue({
    id: 11,
    user_id: 1,
    title: 'New Study Session',
    created_at: '2026-09-23T00:00:00Z',
  }),
  sendChatMessage: vi.fn().mockResolvedValue({
    id: 103,
    session_id: 10,
    assistant_message: {
      id: 103,
      session_id: 10,
      role: 'assistant',
      content: 'Virtual memory isolates process address spaces.',
    },
    reply: 'Virtual memory isolates process address spaces.',
    grounded: true,
    insufficient_evidence: false,
    sources: [],
    provider: 'demo',
    model: 'demo-model',
  }),
  deleteChatSession: vi.fn().mockResolvedValue({ message: 'Deleted', id: 10 }),
}));

vi.mock('../api/resumes', () => ({
  listResumes: vi.fn().mockResolvedValue([
    {
      id: 5,
      user_id: 1,
      original_filename: 'candidate_resume.pdf',
      file_type: 'pdf',
      file_size: 15360,
      processing_status: 'completed',
      parsed_data: {
        skills: ['Python', 'Docker', 'FastAPI'],
      },
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  listResumeAnalyses: vi.fn().mockResolvedValue([
    {
      id: 20,
      resume_id: 5,
      score: 85,
      match_score: 85,
      target_role: 'Backend Engineer',
      extracted_skills: ['Python', 'Docker', 'FastAPI'],
      matched_skills: ['Python', 'FastAPI'],
      missing_skills: ['Kubernetes', 'PostgreSQL'],
      recommendations: ['Build a project with Kubernetes and PostgreSQL.'],
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  uploadResume: vi.fn(),
  deleteResume: vi.fn(),
  analyzeResume: vi.fn(),
}));

vi.mock('../api/career', () => ({
  getCareerProfile: vi.fn().mockResolvedValue({
    id: 1,
    user_id: 1,
    target_role: 'Software Engineer',
    degree: 'B.Tech CS',
    experience: 'Beginner / Student',
    current_skills: ['Python', 'SQL'],
    interests: ['Distributed Systems'],
    created_at: '2026-09-23T00:00:00Z',
  }),
  upsertCareerProfile: vi.fn().mockResolvedValue({
    id: 1,
    user_id: 1,
    target_role: 'Software Engineer',
    degree: 'B.Tech CS',
    experience: 'Beginner / Student',
    current_skills: ['Python', 'SQL', 'TypeScript'],
    interests: ['Distributed Systems'],
    created_at: '2026-09-23T00:00:00Z',
  }),
  listRoadmaps: vi.fn().mockResolvedValue([
    {
      id: 50,
      career_profile_id: 1,
      title: 'Personalized Roadmap: Software Engineer',
      target_role: 'Software Engineer',
      rationale: 'Curated 12-week roadmap for Software Engineer foundations.',
      weekly_plan: [
        {
          week_range: 'Weeks 1-2',
          title: 'Algorithms & Data Structures',
          focus: 'Algorithms & Data Structures',
          description: 'Arrays, Linked Lists, Trees, and Complexity.',
          deliverable: 'Implement 10 LeetCode problems.',
          skills: ['Python', 'Big-O'],
        },
        {
          week_range: 'Weeks 3-4',
          title: 'System Design & REST APIs',
          focus: 'System Design & REST APIs',
          description: 'Build robust REST APIs with FastAPI.',
          deliverable: 'Deploy REST API with docs.',
          skills: ['FastAPI', 'HTTP'],
        },
      ],
      projects: [
        {
          title: 'Distributed Key-Value Store',
          description: 'Build a distributed key-value store with raft consensus.',
          difficulty: 'Intermediate',
          skills: ['Go', 'Raft'],
        },
      ],
      interview_topics: ['Data Structures', 'Database Indexing'],
      created_at: '2026-09-23T00:00:00Z',
    },
  ]),
  generateRoadmap: vi.fn(),
  deleteRoadmap: vi.fn(),
}));

describe('Frontend End-to-End Workflow Views', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders DocumentsPage with uploaded document list', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <DocumentsPage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Operating Systems Ch 1')).toBeInTheDocument();
      expect(screen.getByText('PDF')).toBeInTheDocument();
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });
  });

  it('renders ChatPage with active messages and grounding citations', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <ChatPage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('OS Exam Prep')[0]).toBeInTheDocument();
      expect(screen.getByText('Explain process states')).toBeInTheDocument();
      expect(screen.getByText(/Process states include Ready, Running, and Blocked/i)).toBeInTheDocument();
      expect(screen.getByText(/1 Grounding Source Citations/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Send message' })).toBeVisible();
      expect(screen.getByText('Send')).toBeVisible();
    });

    fireEvent.click(screen.getByRole('button', { name: /^New$/ }));
    expect(await screen.findByRole('heading', { name: 'Start New Study Chat' })).toBeVisible();
    expect(screen.getByRole('button', { name: /^Create Session$/ })).toBeVisible();
  });

  it('renders ResumePage with ATS Score and Matched vs Missing Skills', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <ResumePage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('candidate_resume.pdf')).toBeInTheDocument();
      expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('Strong Match')).toBeInTheDocument();
      expect(screen.getByText('✓ Python')).toBeInTheDocument();
      expect(screen.getByText('+ Kubernetes')).toBeInTheDocument();
      expect(screen.getByText('Targeted for "candidate_resume.pdf"')).toBeInTheDocument();
    });
  });

  it('renders CareerProfilePage with existing user competencies', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <CareerProfilePage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('B.Tech CS')).toBeInTheDocument();
      expect(screen.getByText('Distributed Systems')).toBeInTheDocument();
    });
  });

  it('uses a valid experience selection for a new career profile', async () => {
    vi.mocked(getCareerProfile).mockRejectedValueOnce(new Error('Profile not found'));

    render(
      <MemoryRouter>
        <UserProvider>
          <CareerProfilePage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /experience level/i })).toHaveValue('Beginner / Student');
    });
  });

  it('renders CareerRoadmapPage with 12-week milestones and capstone projects', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <CareerRoadmapPage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Software Engineer')[0]).toBeInTheDocument();
      expect(screen.getByText('Weeks 1-2')).toBeInTheDocument();
      expect(screen.getByText('Algorithms & Data Structures')).toBeInTheDocument();
      expect(screen.getByText('Distributed Key-Value Store')).toBeInTheDocument();
      expect(screen.getByText('Database Indexing')).toBeInTheDocument();
    });
  });

  it('renders DashboardPage with live metric summaries', async () => {
    render(
      <MemoryRouter>
        <UserProvider>
          <DashboardPage />
        </UserProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Welcome to SahayakAI/i)).toBeInTheDocument();
      expect(screen.getByText('Recent Study Documents')).toBeInTheDocument();
      expect(screen.getByText('Active Career Roadmap')).toBeInTheDocument();
    });
  });
});
