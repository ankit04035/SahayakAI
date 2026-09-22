import { SourceReference } from './document';

export interface ChatSessionRead {
  id: number;
  user_id: number;
  title: string;
  document_id?: number | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ChatMessageRead {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  source_metadata?: SourceReference[] | Record<string, any> | null;
  sources?: SourceReference[];
  insufficient_evidence?: boolean;
  created_at: string;
}

export interface ChatResponse {
  id?: number;
  session_id: number;
  user_message: ChatMessageRead;
  assistant_message: ChatMessageRead;
  reply?: string;
  grounded: boolean;
  insufficient_evidence: boolean;
  sources: SourceReference[];
  provider: string;
  model: string;
}
