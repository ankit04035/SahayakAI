export interface DocumentRead {
  id: number;
  user_id: number;
  title?: string | null;
  original_filename: string;
  filename?: string;
  stored_filename: string;
  file_type: string;
  file_size: number;
  mime_type?: string | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed' | string;
  status?: string;
  chunk_count?: number;
  created_at: string;
  updated_at?: string | null;
}

export interface DocumentDetailRead extends DocumentRead {
  extracted_text?: string | null;
  character_count?: number;
  word_count?: number;
  page_count?: number;
  primary_language?: string;
  keywords?: string[];
  stats?: {
    word_count?: number;
    char_count?: number;
    keywords?: string[];
    [key: string]: any;
  };
}

export interface DocumentUploadResponse extends DocumentRead {
  character_count: number;
  word_count: number;
  page_count: number;
  chunk_count: number;
  primary_language: string;
  keywords: string[];
}

export interface DocumentChunkRead {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  character_count: number;
  page_number?: number | null;
  has_embedding?: boolean;
  chunk_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface SourceReference {
  chunk_id: number;
  chunk_index: number;
  page: number;
  page_number?: number | null;
  similarity: number;
  similarity_score?: number;
  content_preview?: string;
}

export interface RAGQueryResponse {
  answer: string;
  grounded: boolean;
  provider: string;
  model: string;
  sources: SourceReference[];
  query: string;
  retrieved_count: number;
  insufficient_evidence: boolean;
}
