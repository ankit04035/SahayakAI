import { apiRequest } from './client';
import { ChatSessionRead, ChatMessageRead, ChatResponse } from '../types/chat';

export async function createChatSession(
  title?: string,
  documentId?: number | null,
  userId?: number
): Promise<ChatSessionRead> {
  return apiRequest<ChatSessionRead>('/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ title, document_id: documentId, user_id: userId }),
    userId,
  });
}

export async function listChatSessions(userId?: number): Promise<ChatSessionRead[]> {
  return apiRequest<ChatSessionRead[]>('/chat/sessions', { userId });
}

export async function getChatSession(sessionId: number, userId?: number): Promise<ChatSessionRead> {
  return apiRequest<ChatSessionRead>(`/chat/sessions/${sessionId}`, { userId });
}

export async function deleteChatSession(sessionId: number, userId?: number): Promise<{ message: string; id: number }> {
  return apiRequest<{ message: string; id: number }>(`/chat/sessions/${sessionId}`, {
    method: 'DELETE',
    userId,
  });
}

export async function sendChatMessage(
  sessionId: number,
  message: string,
  topK?: number,
  similarityThreshold?: number,
  userId?: number
): Promise<ChatResponse> {
  const payload: any = { message };
  if (topK !== undefined) payload.top_k = topK;
  if (similarityThreshold !== undefined) payload.similarity_threshold = similarityThreshold;

  return apiRequest<ChatResponse>(`/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload),
    userId,
  });
}

export async function listChatMessages(sessionId: number, userId?: number): Promise<ChatMessageRead[]> {
  return apiRequest<ChatMessageRead[]>(`/chat/sessions/${sessionId}/messages`, { userId });
}
