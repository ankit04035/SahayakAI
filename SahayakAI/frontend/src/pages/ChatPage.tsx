import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  MessageSquare,
  Send,
  Plus,
  Trash2,
  FileText,
  Sparkles,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  User,
  Bot,
  ExternalLink,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import {
  createChatSession,
  listChatSessions,
  getChatSession,
  deleteChatSession,
  sendChatMessage,
  listChatMessages,
} from '../api/chat';
import { getDocuments } from '../api/documents';
import { ChatSessionRead, ChatMessageRead } from '../types/chat';
import { DocumentRead } from '../types/document';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { formatDate, formatScorePercentage } from '../utils/formatters';

export const ChatPage: React.FC = () => {
  const { userId } = useUser();
  const location = useLocation();

  const [sessions, setSessions] = useState<ChatSessionRead[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSessionRead | null>(null);
  const [messages, setMessages] = useState<ChatMessageRead[]>([]);
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [inputMessage, setInputMessage] = useState('');

  // New session modal
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<number | undefined>(undefined);
  const [creatingSession, setCreatingSession] = useState(false);

  // Citation collapse states per message
  const [expandedCitations, setExpandedCitations] = useState<Record<number, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load documents for session creation binding
  useEffect(() => {
    getDocuments(userId).then(setDocuments).catch(console.error);
  }, [userId]);

  // Load chat sessions
  const fetchSessions = async () => {
    setLoadingSessions(true);
    try {
      const data = await listChatSessions(userId);
      setSessions(data);

      // Check if location.state specified an initial session or doc
      const state = location.state as { activeSessionId?: number; boundDocumentId?: number; boundDocumentTitle?: string } | null;

      if (state?.boundDocumentId) {
        // Automatically open new session modal pre-selected with this doc
        setSelectedDocId(state.boundDocumentId);
        setNewTitle(`Chat: ${state.boundDocumentTitle || 'Document'}`);
        setIsNewModalOpen(true);
      } else if (state?.activeSessionId) {
        const found = data.find((s) => s.id === state.activeSessionId);
        if (found) {
          setActiveSession(found);
          loadMessages(found.id);
        } else if (data.length > 0) {
          setActiveSession(data[0]);
          loadMessages(data[0].id);
        }
      } else if (data.length > 0 && !activeSession) {
        setActiveSession(data[0]);
        loadMessages(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [userId]);

  const loadMessages = async (sessionId: number) => {
    setLoadingMessages(true);
    try {
      const msgs = await listChatMessages(sessionId, userId);
      setMessages(msgs);
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSelectSession = (session: ChatSessionRead) => {
    setActiveSession(session);
    loadMessages(session.id);
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingSession(true);
    try {
      const newSession = await createChatSession(
        newTitle.trim() || undefined,
        selectedDocId,
        userId
      );
      setSessions((prev) => [newSession, ...prev]);
      setActiveSession(newSession);
      setMessages([]);
      setIsNewModalOpen(false);
      setNewTitle('');
      setSelectedDocId(undefined);
    } catch (err: any) {
      alert(`Failed to create session: ${err.message}`);
    } finally {
      setCreatingSession(false);
    }
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    try {
      await deleteChatSession(sessionId, userId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (activeSession?.id === sessionId) {
        if (remaining.length > 0) {
          setActiveSession(remaining[0]);
          loadMessages(remaining[0].id);
        } else {
          setActiveSession(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || !activeSession || sending) return;

    const userText = inputMessage.trim();
    setInputMessage('');
    setSending(true);

    // Optimistically add user message
    const tempUserMsg: ChatMessageRead = {
      id: Date.now(),
      session_id: activeSession.id,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await sendChatMessage(activeSession.id, userText, 5, 0.35, userId);
      // Append assistant reply from response
      const assistantMsg: ChatMessageRead = {
        id: response.assistant_message?.id || Date.now() + 1,
        session_id: activeSession.id,
        role: 'assistant',
        content: response.assistant_message?.content || response.reply || '',
        sources: response.sources,
        insufficient_evidence: response.insufficient_evidence,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessageRead = {
        id: Date.now() + 2,
        session_id: activeSession.id,
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to generate response'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const toggleCitation = (msgId: number) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col md:flex-row bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Left Sidebar: Session List */}
      <div className="w-full md:w-80 border-r border-gray-200 flex flex-col bg-gray-50/50 shrink-0">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-gray-900 text-sm">Study Chats</h2>
            <p className="text-2xs text-gray-500">Document-grounded sessions</p>
          </div>
          <Button
            size="sm"
            onClick={() => {
              setNewTitle('');
              setSelectedDocId(undefined);
              setIsNewModalOpen(true);
            }}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            New
          </Button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loadingSessions ? (
            <div className="py-8 text-center">
              <LoadingSpinner size="sm" label="Loading sessions..." />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-10 px-4">
              <MessageSquare className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-gray-600">No chat sessions</p>
              <p className="text-2xs text-gray-400 mt-1 mb-3">Create your first session to study with AI.</p>
              <Button size="sm" variant="outline" onClick={() => setIsNewModalOpen(true)}>
                Create Session
              </Button>
            </div>
          ) : (
            sessions.map((session) => {
              const isSelected = activeSession?.id === session.id;
              return (
                <div
                  key={session.id}
                  onClick={() => handleSelectSession(session)}
                  className={`group flex items-start justify-between p-3 rounded-xl cursor-pointer transition ${
                    isSelected
                      ? 'bg-primary-50/80 border border-primary-200 text-primary-900 shadow-2xs'
                      : 'hover:bg-gray-100/70 text-gray-700'
                  }`}
                >
                  <div className="min-w-0 flex-1 mr-2">
                    <h3 className={`text-xs font-semibold truncate ${isSelected ? 'text-primary-900' : 'text-gray-800'}`}>
                      {session.title || `Chat Session #${session.id}`}
                    </h3>
                    <div className="flex items-center gap-1.5 mt-1 text-2xs text-gray-400">
                      <span>{formatDate(session.created_at)}</span>
                      {session.document_id && (
                        <>
                          <span>•</span>
                          <span className="text-primary-600 font-medium truncate">Doc #{session.document_id}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 transition rounded"
                    title="Delete session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Column: Chat Window */}
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {activeSession ? (
          <>
            {/* Chat Header */}
            <div className="px-6 py-3.5 border-b border-gray-200 flex items-center justify-between bg-white z-10">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-gray-900 truncate">
                    {activeSession.title || `Chat Session #${activeSession.id}`}
                  </h3>
                  {activeSession.document_id ? (
                    <Badge variant="primary" size="sm">
                      <FileText className="w-3 h-3 mr-1" />
                      Grounded in Doc #{activeSession.document_id}
                    </Badge>
                  ) : (
                    <Badge variant="neutral" size="sm">
                      General Academic Chat
                    </Badge>
                  )}
                </div>
                <p className="text-2xs text-gray-400 mt-0.5">
                  Started {formatDate(activeSession.created_at)} • Ask any syllabus question
                </p>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-gray-50/30">
              {loadingMessages ? (
                <div className="py-20 text-center">
                  <LoadingSpinner size="md" label="Loading messages..." />
                </div>
              ) : messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="w-12 h-12 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center mb-3 shadow-xs">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-bold text-gray-900 mb-1">
                    Ask SahayakAI anything about your studies
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mb-6">
                    {activeSession.document_id
                      ? 'This session is grounded in your uploaded document. Questions are verified against its vector embeddings.'
                      : 'Ask concepts, explanations, practice questions, or study strategies.'}
                  </p>

                  {/* Suggestion prompts */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
                    {[
                      'Summarize the core topics in simple terms',
                      'What are the key formulas or definitions?',
                      'Generate 3 practice quiz questions with answers',
                      'Explain the most challenging concept step-by-step',
                    ].map((prompt, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setInputMessage(prompt);
                        }}
                        className="text-left p-3 text-xs bg-white rounded-lg border border-gray-200 hover:border-primary-400 hover:bg-primary-50/30 text-gray-700 transition"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  const hasSources = msg.sources && msg.sources.length > 0;
                  const isExpanded = !!expandedCitations[msg.id];

                  return (
                    <div
                      key={msg.id}
                      className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
                    >
                      {!isUser && (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-2xs">
                          <Bot className="w-4 h-4" />
                        </div>
                      )}

                      <div className={`space-y-2 max-w-[85%] sm:max-w-xl`}>
                        <div
                          className={`p-4 rounded-2xl text-sm leading-relaxed ${
                            isUser
                              ? 'bg-primary-600 text-white rounded-tr-none shadow-sm'
                              : 'bg-white text-gray-900 border border-gray-200 rounded-tl-none shadow-2xs'
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>

                        {/* Insufficient Evidence Notice */}
                        {!isUser && msg.insufficient_evidence && (
                          <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-2xs text-amber-800 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                            <span>
                              Model identified insufficient grounded evidence in document chunks for complete verification.
                            </span>
                          </div>
                        )}

                        {/* Citations Drawer */}
                        {!isUser && hasSources && (
                          <div className="bg-gray-50 border border-gray-200 rounded-xl overflow-hidden text-xs">
                            <button
                              onClick={() => toggleCitation(msg.id)}
                              className="w-full px-3 py-2 flex items-center justify-between text-gray-600 hover:bg-gray-100/60 transition"
                            >
                              <span className="font-semibold flex items-center gap-1.5 text-2xs text-primary-700">
                                <Sparkles className="w-3 h-3" />
                                {msg.sources?.length} Grounding Source Citations
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                              )}
                            </button>

                            {isExpanded && (
                              <div className="p-3 border-t border-gray-200 space-y-2 max-h-60 overflow-y-auto">
                                {msg.sources?.map((src: any, idx: number) => (
                                  <div key={idx} className="bg-white p-2.5 rounded border border-gray-200 text-2xs">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="font-bold text-gray-800">Chunk #{src.chunk_index}</span>
                                      <span className="font-semibold text-emerald-600">
                                        {formatScorePercentage(src.similarity_score)} match
                                      </span>
                                    </div>
                                    {src.page_number !== null && (
                                      <p className="text-gray-400 mb-1">Page {src.page_number}</p>
                                    )}
                                    <p className="text-gray-600 italic bg-gray-50 p-2 rounded">
                                      "{src.content_preview}"
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        <span className="text-2xs text-gray-400 block px-1">
                          {formatDate(msg.created_at)}
                        </span>
                      </div>

                      {isUser && (
                        <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center shrink-0">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  );
                })
              )}

              {sending && (
                <div className="flex gap-3 items-center text-xs text-gray-500 py-2">
                  <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center shrink-0 animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <span className="italic">Assistant is retrieving vector context and generating response...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input Bar */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <form onSubmit={handleSendMessage} className="flex items-end gap-2">
                <textarea
                  rows={2}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask a question about your study material... (Press Enter to send)"
                  className="flex-1 p-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                  disabled={sending}
                />
                <Button
                  type="submit"
                  isLoading={sending}
                  disabled={!inputMessage.trim()}
                  className="h-11 px-4 rounded-xl shrink-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="w-12 h-12 text-gray-300 mb-3" />
            <h3 className="text-base font-semibold text-gray-900 mb-1">No Active Chat Session</h3>
            <p className="text-xs text-gray-500 max-w-sm mb-4">
              Select an existing chat session from the left sidebar or create a new session.
            </p>
            <Button onClick={() => setIsNewModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
              Create New Chat
            </Button>
          </div>
        )}
      </div>

      {/* New Session Modal */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => !creatingSession && setIsNewModalOpen(false)}
        title="Start New Study Chat"
        description="Choose a title and optionally link a study document for RAG-grounded responses."
        maxWidth="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsNewModalOpen(false)} disabled={creatingSession}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateSession} isLoading={creatingSession}>
              Create Session
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Session Title (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Operating Systems Midterm Prep"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Link Study Document (Recommended for RAG)
            </label>
            <select
              value={selectedDocId ?? ''}
              onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">No Document (General Academic Assistant)</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  Doc #{doc.id}: {doc.title || doc.original_filename || doc.filename} ({doc.file_type.toUpperCase()})
                </option>
              ))}
            </select>
            <p className="text-2xs text-gray-500 mt-1">
              Binding a document enables vector similarity search and citation grounding.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
