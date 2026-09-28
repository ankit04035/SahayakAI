import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { UserProvider } from '../context/UserContext';
import App from '../App';

// Mock health and data APIs to avoid network errors during testing
vi.mock('../api/auth', () => ({
  getCurrentUser: vi.fn().mockRejectedValue(new Error('Unauthenticated')),
  registerAccount: vi.fn().mockResolvedValue({ id: 7, name: 'Ada Student', email: 'ada@example.com', created_at: '2026-09-28T00:00:00Z' }),
  loginAccount: vi.fn(),
  logoutAccount: vi.fn(),
}));

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

  it('shows register and sign-in actions to signed-out visitors', async () => {
    render(
      <UserProvider>
        <App />
      </UserProvider>
    );

    expect(await screen.findByRole('button', { name: 'Register' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Study Documents' })).not.toBeInTheDocument();
  });

  it('registers an account and unlocks the workspace', async () => {
    render(
      <UserProvider>
        <App />
      </UserProvider>
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Register' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Ada Student' } });
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'ada@example.com' } });
    fireEvent.change(screen.getByLabelText(/Password/), { target: { value: 'correct-horse-battery-17' } });
    const createButtons = screen.getAllByRole('button', { name: 'Create account' });
    fireEvent.click(createButtons[createButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Welcome to SahayakAI' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Study Documents' })).toBeInTheDocument();
    });
  });
});
