import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Layers,
  Sparkles,
  Search,
  MessageSquare,
  Trash2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Copy,
  Check,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getDocument, getDocumentChunks, embedDocumentChunks, askDocumentQuestion, deleteDocument } from '../api/documents';
import { DocumentDetailRead, DocumentChunkRead, RAGQueryResponse } from '../types/document';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import { formatDate, formatFileSize, formatScorePercentage } from '../utils/formatters';

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const documentId = Number(id);
  const { userId } = useUser();
  const navigate = useNavigate();

  const [document, setDocument] = useState<DocumentDetailRead | null>(null);
  const [chunks, setChunks] = useState<DocumentChunkRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'chunks' | 'ask'>('overview');

  // Embed action
  const [embedding, setEmbedding] = useState(false);
  const [embedMessage, setEmbedMessage] = useState<string | null>(null);

  // Direct Q&A
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.35);
  const [asking, setAsking] = useState(false);
  const [qaResult, setQaResult] = useState<RAGQueryResponse | null>(null);
  const [qaError, setQaError] = useState<string | null>(null);

  // Delete modal
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Copy chunk helper
  const [copiedChunkId, setCopiedChunkId] = useState<number | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadDetails = async () => {
      setLoading(true);
      try {
        const [docData, chunksData] = await Promise.all([
          getDocument(documentId, userId),
          getDocumentChunks(documentId, userId, 0, 100),
        ]);
        if (isMounted) {
          setDocument(docData);
          setChunks(chunksData);
        }
      } catch (err: any) {
        console.error('Failed to load document details:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    if (documentId) loadDetails();
    return () => {
      isMounted = false;
    };
  }, [documentId, userId]);

  const handleEmbedChunks = async () => {
    setEmbedding(true);
    setEmbedMessage(null);
    try {
      const res = await embedDocumentChunks(documentId, userId);
      setEmbedMessage(`Successfully embedded ${res.embedded_chunks} chunks into vector index.`);
      // Refresh chunks
      const updatedChunks = await getDocumentChunks(documentId, userId, 0, 100);
      setChunks(updatedChunks);
    } catch (err: any) {
      setEmbedMessage(`Embedding failed: ${err.message}`);
    } finally {
      setEmbedding(false);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setAsking(true);
    setQaError(null);
    try {
      const res = await askDocumentQuestion(documentId, question.trim(), topK, similarityThreshold, userId);
      setQaResult(res);
    } catch (err: any) {
      setQaError(err.message || 'Error executing grounded question query');
    } finally {
      setAsking(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteDocument(documentId, userId);
      navigate('/documents');
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
      setDeleting(false);
    }
  };

  const handleCopyChunk = (chunkId: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(chunkId);
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <LoadingSpinner size="lg" label="Loading document details and vector chunks..." />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-16">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-gray-900">Document Not Found</h2>
        <p className="text-sm text-gray-500 mt-1 mb-4">The requested document does not exist or belongs to another user.</p>
        <Link to="/documents">
          <Button variant="secondary" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Back to Documents
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/documents">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 truncate max-w-md sm:max-w-xl">
              {document.title || document.original_filename || (document.original_filename || document.filename)}
            </h1>
            <p className="text-2xs text-gray-500 mt-0.5">
              ID: #{document.id} • {(document.original_filename || document.filename)} • Uploaded {formatDate(document.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/chat" state={{ boundDocumentId: document.id, boundDocumentTitle: document.title || document.original_filename || (document.original_filename || document.filename) }}>
            <Button size="sm" variant="outline" leftIcon={<MessageSquare className="w-3.5 h-3.5" />}>
              Open in Chat
            </Button>
          </Link>
          <Button size="sm" variant="danger" onClick={() => setIsDeleteModalOpen(true)} leftIcon={<Trash2 className="w-3.5 h-3.5" />}>
            Delete
          </Button>
        </div>
      </div>

      {embedMessage && (
        <Alert
          type="info"
          message={embedMessage}
          onClose={() => setEmbedMessage(null)}
        />
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 flex gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'overview'
              ? 'border-primary-600 text-primary-600 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Document Overview
        </button>
        <button
          onClick={() => setActiveTab('chunks')}
          className={`pb-3 border-b-2 transition flex items-center gap-1.5 ${
            activeTab === 'chunks'
              ? 'border-primary-600 text-primary-600 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <span>Vector Chunks</span>
          <Badge size="sm" variant="neutral">{chunks.length}</Badge>
        </button>
        <button
          onClick={() => setActiveTab('ask')}
          className={`pb-3 border-b-2 transition flex items-center gap-1.5 ${
            activeTab === 'ask'
              ? 'border-primary-600 text-primary-600 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-primary-500" />
          <span>Direct RAG Q&A</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card title="Document Statistics">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <span className="text-2xs font-semibold text-gray-400 uppercase">File Format</span>
                  <p className="text-lg font-bold text-gray-900 mt-1">{document.file_type.toUpperCase()}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <span className="text-2xs font-semibold text-gray-400 uppercase">File Size</span>
                  <p className="text-lg font-bold text-gray-900 mt-1">{formatFileSize(document.file_size)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <span className="text-2xs font-semibold text-gray-400 uppercase">Total Pages</span>
                  <p className="text-lg font-bold text-gray-900 mt-1">{document.page_count ?? 1}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <span className="text-2xs font-semibold text-gray-400 uppercase">Total Chunks</span>
                  <p className="text-lg font-bold text-gray-900 mt-1">{chunks.length}</p>
                </div>
              </div>

              {((document.keywords || document.stats?.keywords || [])).length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <h4 className="text-xs font-semibold text-gray-700 mb-3">Extracted Core Keywords</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(document.keywords || document.stats?.keywords || []).map((kw: string, i: number) => (
                      <Badge key={i} variant="primary" size="sm">
                        {kw}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            <Card title="Embeddings & Vector Index Status">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-800">Chunk Vector Embeddings</h4>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Embeddings are generated with SentenceTransformers (all-MiniLM-L6-v2) for cosine similarity ranking.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleEmbedChunks}
                  isLoading={embedding}
                  leftIcon={<Sparkles className="w-3.5 h-3.5 text-primary-600" />}
                >
                  Regenerate Embeddings
                </Button>
              </div>
            </Card>
          </div>

          <div className="space-y-6">
            <Card title="Processing Details">
              <dl className="divide-y divide-gray-100 text-xs">
                <div className="py-2 flex justify-between">
                  <dt className="text-gray-500">Document ID</dt>
                  <dd className="font-medium text-gray-900">#{document.id}</dd>
                </div>
                <div className="py-2 flex justify-between">
                  <dt className="text-gray-500">Status</dt>
                  <dd>
                    <Badge variant={document.processing_status === 'PROCESSED' ? 'success' : 'neutral'} size="sm">
                      {document.processing_status}
                    </Badge>
                  </dd>
                </div>
                <div className="py-2 flex justify-between">
                  <dt className="text-gray-500">Owner User ID</dt>
                  <dd className="font-medium text-gray-900">{document.user_id}</dd>
                </div>
                <div className="py-2 flex justify-between">
                  <dt className="text-gray-500">Created At</dt>
                  <dd className="font-medium text-gray-900">{formatDate(document.created_at)}</dd>
                </div>
              </dl>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: CHUNK INSPECTOR */}
      {activeTab === 'chunks' && (
        <Card
          title={`Chunks (${chunks.length})`}
          subtitle="Inspect partitioned text passages and their vector embedding metadata"
        >
          <div className="space-y-3">
            {chunks.map((chunk) => (
              <div
                key={chunk.id}
                className="p-4 rounded-lg border border-gray-200 bg-gray-50/50 hover:bg-white hover:border-primary-200 transition"
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900">Chunk #{chunk.chunk_index}</span>
                    {(chunk.page_number ?? (chunk.chunk_metadata?.page_number as number | undefined)) !== null && (
                      <Badge variant="neutral" size="sm">Page {(chunk.page_number ?? (chunk.chunk_metadata?.page_number as number | undefined))}</Badge>
                    )}
                    <Badge variant={(chunk.has_embedding ?? (chunk.chunk_metadata?.has_embedding as boolean | undefined)) ? 'success' : 'warning'} size="sm">
                      {(chunk.has_embedding ?? (chunk.chunk_metadata?.has_embedding as boolean | undefined)) ? 'Vector Indexed' : 'No Embedding'}
                    </Badge>
                  </div>
                  <button
                    onClick={() => handleCopyChunk(chunk.id, chunk.content)}
                    className="text-gray-400 hover:text-gray-600 flex items-center gap-1 text-2xs p-1 rounded"
                    title="Copy chunk text"
                  >
                    {copiedChunkId === chunk.id ? (
                      <>
                        <Check className="w-3 h-3 text-green-600" />
                        <span className="text-green-600">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed bg-white p-3 rounded border border-gray-100">
                  {chunk.content}
                </p>
                <div className="mt-2 text-2xs text-gray-400 flex items-center gap-3">
                  <span>Characters: {chunk.content.length}</span>
                  <span>Approx Tokens: {Math.round(chunk.content.length / 4)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 3: DIRECT RAG Q&A */}
      {activeTab === 'ask' && (
        <div className="space-y-6">
          <Card
            title="Ask Questions Grounded in this Document"
            subtitle="Queries are strictly evaluated against this document's vector chunks"
          >
            <form onSubmit={handleAskQuestion} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Your Question:
                </label>
                <textarea
                  rows={3}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. What are the core topics discussed in this chapter?"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Advanced Retrieval Settings */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-gray-50 p-3 rounded-lg border border-gray-200">
                <div>
                  <label className="block text-2xs font-semibold text-gray-600 mb-1">
                    Top-K Context Chunks: <span className="text-primary-600">{topK}</span>
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="w-full accent-primary-600 cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-2xs font-semibold text-gray-600 mb-1">
                    Similarity Threshold: <span className="text-primary-600">{similarityThreshold}</span>
                  </label>
                  <input
                    type="range"
                    min={0.1}
                    max={0.9}
                    step={0.05}
                    value={similarityThreshold}
                    onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                    className="w-full accent-primary-600 cursor-pointer"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button type="submit" isLoading={asking} disabled={!question.trim()} leftIcon={<Sparkles className="w-4 h-4" />}>
                  Run Grounded Query
                </Button>
              </div>
            </form>

            {qaError && <Alert type="error" message={qaError} className="mt-4" />}

            {/* Q&A Result */}
            {qaResult && (
              <div className="mt-6 pt-6 border-t border-gray-200 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-primary-600" />
                    Generated Answer
                  </h4>
                  <Badge variant={qaResult.insufficient_evidence ? 'warning' : 'success'} size="sm">
                    {qaResult.insufficient_evidence ? 'Insufficient Evidence' : `${qaResult.sources.length} Sources Found`}
                  </Badge>
                </div>

                <div className="bg-primary-50/40 border border-primary-100 p-4 rounded-xl text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {qaResult.answer}
                </div>

                {/* Grounding Source references */}
                {qaResult.sources.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <h5 className="text-xs font-semibold text-gray-700">Source References:</h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {qaResult.sources.map((src, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-primary-700">Chunk #{src.chunk_index}</span>
                            <span className="text-2xs font-semibold text-emerald-600">
                              {formatScorePercentage((src.similarity_score ?? src.similarity))} Match
                            </span>
                          </div>
                          {(src.page_number ?? src.page) !== null && (
                            <p className="text-2xs text-gray-400">Page: {(src.page_number ?? src.page)}</p>
                          )}
                          <p className="text-2xs text-gray-600 line-clamp-3 italic">
                            "{src.content_preview || 'Chunk preview'}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => !deleting && setIsDeleteModalOpen(false)}
        title="Delete Document"
        maxWidth="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={deleting}>
              Delete Document
            </Button>
          </>
        }
      >
        <p className="text-sm text-gray-600">
          Are you sure you want to permanently delete <strong>{document.title || document.original_filename || (document.original_filename || document.filename)}</strong>? All chunks and vector indexes will be removed immediately.
        </p>
      </Modal>
    </div>
  );
};
