import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Upload,
  FileText,
  Trash2,
  ExternalLink,
  MessageSquare,
  Search,
  AlertCircle,
  CheckCircle2,
  File,
  Layers,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getDocuments, uploadDocument, deleteDocument } from '../api/documents';
import { DocumentRead } from '../types/document';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Alert } from '../components/common/Alert';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { formatDate, formatFileSize } from '../utils/formatters';

export const DocumentsPage: React.FC = () => {
  const { userId } = useUser();
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Upload modal state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [titleInput, setTitleInput] = useState('');
  const [autoEmbed, setAutoEmbed] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Delete modal state
  const [docToDelete, setDocToDelete] = useState<DocumentRead | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await getDocuments(userId);
      setDocuments(data);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [userId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setTitleInput(file.name.replace(/\.[^/.]+$/, ''));
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'pdf' || ext === 'txt') {
        setSelectedFile(file);
        setTitleInput(file.name.replace(/\.[^/.]+$/, ''));
        setUploadError(null);
      } else {
        setUploadError('Only .pdf and .txt files are supported.');
      }
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a PDF or TXT file to upload.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const res = await uploadDocument(selectedFile, titleInput.trim() || undefined, autoEmbed, userId);
      setUploadSuccess(`Successfully processed "${res.title}" with ${res.chunk_count} chunks.`);
      setSelectedFile(null);
      setTitleInput('');
      fetchDocs();
      setTimeout(() => {
        setIsUploadModalOpen(false);
        setUploadSuccess(null);
      }, 1500);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!docToDelete) return;
    setDeleting(true);
    try {
      await deleteDocument(docToDelete.id, userId);
      setDocuments((prev) => prev.filter((d) => d.id !== docToDelete.id));
      setDocToDelete(null);
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeleting(false);
    }
  };

  const filteredDocs = documents.filter((doc) =>
    ((doc.title || doc.original_filename || doc.filename || '') as string).toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Study Documents</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage course materials, lecture notes, and textbooks grounded into vector retrieval.
          </p>
        </div>
        <Button
          onClick={() => {
            setSelectedFile(null);
            setTitleInput('');
            setUploadError(null);
            setUploadSuccess(null);
            setIsUploadModalOpen(true);
          }}
          leftIcon={<Upload className="w-4 h-4" />}
        >
          Upload Document
        </Button>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documents by title or filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
          />
        </div>
      </div>

      {/* Documents Table / Content */}
      {loading ? (
        <div className="py-16 text-center">
          <LoadingSpinner size="lg" label="Loading documents..." />
        </div>
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-8 h-8 text-primary-500" />}
          title={searchQuery ? 'No documents match your query' : 'No documents uploaded yet'}
          description={
            searchQuery
              ? 'Try adjusting your search criteria.'
              : 'Upload syllabus PDFs, lecture slides, or TXT notes to power your Study Assistant.'
          }
          action={
            !searchQuery && (
              <Button size="sm" onClick={() => setIsUploadModalOpen(true)} leftIcon={<Upload className="w-4 h-4" />}>
                Upload Document
              </Button>
            )
          }
        />
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50/80 text-2xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Document</th>
                  <th scope="col" className="px-6 py-3.5">Format</th>
                  <th scope="col" className="px-6 py-3.5">Size</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5">Uploaded</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50/80 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="min-w-0 max-w-xs sm:max-w-md">
                          <Link
                            to={`/documents/${doc.id}`}
                            className="font-semibold text-gray-900 hover:text-primary-600 truncate block transition"
                          >
                            {doc.title || doc.original_filename || (doc.original_filename || doc.filename)}
                          </Link>
                          <span className="text-2xs text-gray-400 truncate block">{(doc.original_filename || doc.filename)}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="neutral" size="sm">
                        {doc.file_type.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500 whitespace-nowrap">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant={doc.processing_status === 'PROCESSED' ? 'success' : doc.processing_status === 'CHUNKING' ? 'warning' : 'danger'}
                        size="sm"
                      >
                        {doc.processing_status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500 whitespace-nowrap">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/documents/${doc.id}`}>
                          <Button size="sm" variant="outline" className="text-xs">
                            Inspect
                          </Button>
                        </Link>
                        <Link to="/chat" state={{ boundDocumentId: doc.id, boundDocumentTitle: doc.title || doc.original_filename || (doc.original_filename || doc.filename) }}>
                          <Button size="sm" variant="ghost" title="Start Chat with Document" className="text-primary-600 hover:text-primary-700">
                            <MessageSquare className="w-4 h-4" />
                          </Button>
                        </Link>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setDocToDelete(doc)}
                          title="Delete Document"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => !uploading && setIsUploadModalOpen(false)}
        title="Upload Study Document"
        description="Upload academic course notes, papers, or textbooks for RAG retrieval."
        maxWidth="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsUploadModalOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUploadSubmit} isLoading={uploading} disabled={!selectedFile}>
              Upload & Process
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {uploadError && <Alert type="error" message={uploadError} />}
          {uploadSuccess && <Alert type="success" message={uploadSuccess} />}

          {/* Drag & drop box */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
              selectedFile ? 'border-primary-500 bg-primary-50/20' : 'border-gray-300 hover:border-primary-400 bg-gray-50/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.txt"
              className="hidden"
            />
            <div className="w-10 h-10 rounded-full bg-white shadow-xs mx-auto flex items-center justify-center text-primary-600 mb-2">
              <Upload className="w-5 h-5" />
            </div>
            {selectedFile ? (
              <div>
                <p className="text-sm font-semibold text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500 mt-1">{formatFileSize(selectedFile.size)}</p>
                <p className="text-2xs text-primary-600 mt-2 font-medium">Click to select different file</p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Drag and drop your file here, or <span className="text-primary-600 font-semibold">browse</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">Supports PDF and TXT files up to 10MB</p>
              </div>
            )}
          </div>

          {/* Title Input */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Document Title (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. CS101 Operating Systems Chapter 4"
              value={titleInput}
              onChange={(e) => setTitleInput(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Auto-embed toggle */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="auto-embed-toggle"
              checked={autoEmbed}
              onChange={(e) => setAutoEmbed(e.target.checked)}
              className="rounded text-primary-600 focus:ring-primary-500 h-4 w-4"
            />
            <label htmlFor="auto-embed-toggle" className="text-xs text-gray-700 select-none">
              Automatically generate vector embeddings for chunks
            </label>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!docToDelete}
        onClose={() => !deleting && setDocToDelete(null)}
        title="Delete Document"
        description="Are you sure you want to delete this study document?"
        maxWidth="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDocToDelete(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteConfirm} isLoading={deleting}>
              Delete Document
            </Button>
          </>
        }
      >
        <p className="text-sm text-gray-600">
          This will permanently remove <strong>{docToDelete?.title || docToDelete?.filename}</strong> and all of its associated vector chunks. Any linked chat sessions will be preserved.
        </p>
      </Modal>
    </div>
  );
};
