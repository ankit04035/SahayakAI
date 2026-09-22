import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UserProvider } from '../context/UserContext';
import App from '../App';

// Mock health and data APIs to avoid network errors during testing
vi.mock('../api/health', () => ({
  getHealth: vi.fn().mockResolvedValue({
    status: 'ok',
    demo_mode: true,
    ai_provider: 'demo',
    timestamp: '2026-09-23T00:00:00Z',
  }),
}));

vi.mock('../api/documents', () => ({
  getDocuments: vi.fn().mockResolvedValue([]),
}));

vi.mock('../api/chat', () => ({
  listChatSessions: vi.fn().mockResolvedValue([]),
}));

vi.mock('../api/resumes', () => ({
  listResumes: vi.fn().mockResolvedValue([]),
}));

vi.mock('../api/career', () => ({
  getCareerProfile: vi.fn().mockResolvedValue(null),
  listRoadmaps: vi.fn().mockResolvedValue([]),
}));

describe('SahayakAI Frontend App', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the brand title and navigation links', async () => {
    render(
      <UserProvider>
        <App />
      </UserProvider>
    );

    // Brand and subtitle
    expect(screen.getAllByText(/Sahayak/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Student Assistant/i)[0]).toBeInTheDocument();

    // Primary navigation links in sidebar
    expect(screen.getAllByText(/Dashboard/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Study Documents/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Study Assistant/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Resume Analyzer/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Career Profile/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Career Roadmap/i)[0]).toBeInTheDocument();
  });

  it('renders dev user selector with default user #1', () => {
    render(
      <UserProvider>
        <App />
      </UserProvider>
    );

    const userSelect = screen.getByRole('combobox') as HTMLSelectElement;
    expect(userSelect).toBeInTheDocument();
    expect(userSelect.value).toBe('1');
  });
});
