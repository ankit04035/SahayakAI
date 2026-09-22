import { apiRequest } from './client';
import {
  DocumentRead,
  DocumentDetailRead,
  DocumentUploadResponse,
  DocumentChunkRead,
  RAGQueryResponse,
} from '../types/document';

export async function uploadDocument(
  file: File,
  title?: string,
  autoEmbed: boolean = true,
  userId?: number
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  formData.append('auto_embed', String(autoEmbed));
  if (userId) formData.append('user_id', String(userId));

  return apiRequest<DocumentUploadResponse>('/documents/upload', {
    method: 'POST',
    body: formData,
    userId,
  });
}

export async function getDocuments(userId?: number, skip: number = 0, limit: number = 50): Promise<DocumentRead[]> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (userId) params.append('user_id', String(userId));
  return apiRequest<DocumentRead[]>(`/documents?${params.toString()}`, { userId });
}

export async function getDocument(documentId: number, userId?: number): Promise<DocumentDetailRead> {
  return apiRequest<DocumentDetailRead>(`/documents/${documentId}`, { userId });
}

export async function getDocumentChunks(
  documentId: number,
  userId?: number,
  skip: number = 0,
  limit: number = 50
): Promise<DocumentChunkRead[]> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  return apiRequest<DocumentChunkRead[]>(`/documents/${documentId}/chunks?${params.toString()}`, { userId });
}

export async function deleteDocument(documentId: number, userId?: number): Promise<{ message: string; id: number }> {
  return apiRequest<{ message: string; id: number }>(`/documents/${documentId}`, {
    method: 'DELETE',
    userId,
  });
}

export async function embedDocumentChunks(
  documentId: number,
  userId?: number
): Promise<{ document_id: number; embedded_chunks: number; status: string }> {
  return apiRequest(`/documents/${documentId}/embed`, {
    method: 'POST',
    userId,
  });
}

export async function askDocumentQuestion(
  documentId: number,
  question: string,
  topK: number = 5,
  similarityThreshold: number = 0.35,
  userId?: number
): Promise<RAGQueryResponse> {
  return apiRequest<RAGQueryResponse>(`/documents/${documentId}/ask`, {
    method: 'POST',
    body: JSON.stringify({ question, top_k: topK, similarity_threshold: similarityThreshold }),
    userId,
  });
}
