import React, { useState, useEffect, useRef } from 'react';
import {
  Award,
  Upload,
  FileText,
  Trash2,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Briefcase,
  TrendingUp,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import {
  uploadResume,
  listResumes,
  getResume,
  deleteResume,
  analyzeResume,
  listResumeAnalyses,
} from '../api/resumes';
import { ResumeRead, ResumeAnalysisRead } from '../types/resume';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { formatDate, formatFileSize, formatScorePercentage } from '../utils/formatters';

export const ResumePage: React.FC = () => {
  const { userId } = useUser();
  const [resumes, setResumes] = useState<ResumeRead[]>([]);
  const [selectedResume, setSelectedResume] = useState<ResumeRead | null>(null);
  const [loading, setLoading] = useState(true);

  // Upload state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Analysis state
  const [jobDescription, setJobDescription] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [activeAnalysis, setActiveAnalysis] = useState<ResumeAnalysisRead | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<ResumeAnalysisRead[]>([]);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchResumes = async () => {
    setLoading(true);
    try {
      const data = await listResumes(userId);
      setResumes(data);
      if (data.length > 0 && !selectedResume) {
        selectResume(data[0]);
      }
    } catch (err) {
      console.error('Failed to load resumes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, [userId]);

  const selectResume = async (resume: ResumeRead) => {
    setSelectedResume(resume);
    setActiveAnalysis(null);
    try {
      const analyses = await listResumeAnalyses(resume.id, userId);
      setAnalysisHistory(analyses);
      if (analyses.length > 0) {
        setActiveAnalysis(analyses[0]);
      }
    } catch (err) {
      console.error('Failed to load resume analyses:', err);
    }
  };

  const handleUploadResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError(null);
    try {
      const newResume = await uploadResume(uploadFile, userId);
      setResumes((prev) => [newResume, ...prev]);
      selectResume(newResume);
      setIsUploadModalOpen(false);
      setUploadFile(null);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteResume = async (resumeId: number) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await deleteResume(resumeId, userId);
      const remaining = resumes.filter((r) => r.id !== resumeId);
      setResumes(remaining);
      if (selectedResume?.id === resumeId) {
        if (remaining.length > 0) {
          selectResume(remaining[0]);
        } else {
          setSelectedResume(null);
          setActiveAnalysis(null);
          setAnalysisHistory([]);
        }
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResume) return;

    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const result = await analyzeResume(selectedResume.id, jobDescription.trim() || undefined, userId);
      setActiveAnalysis(result);
      setAnalysisHistory((prev) => [result, ...prev]);
    } catch (err: any) {
      setAnalysisError(err.message || 'ATS analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  // ATS Score Color formatting
  const getScoreBadge = (score: number) => {
    if (score >= 80) {
      return { variant: 'success' as const, label: 'Strong Match' };
    }
    if (score >= 60) {
      return { variant: 'warning' as const, label: 'Moderate Match' };
    }
    return { variant: 'danger' as const, label: 'Needs Improvement' };
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Resume Analyzer & ATS Scorecard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Extract skills and structured experience, then benchmark against target job descriptions.
          </p>
        </div>
        <Button
          onClick={() => {
            setUploadFile(null);
            setUploadError(null);
            setIsUploadModalOpen(true);
          }}
          leftIcon={<Upload className="w-4 h-4" />}
        >
          Upload Resume
        </Button>
      </div>

      {loading ? (
        <div className="py-20 text-center">
          <LoadingSpinner size="lg" label="Loading resumes..." />
        </div>
      ) : resumes.length === 0 ? (
        <EmptyState
          icon={<Award className="w-8 h-8 text-primary-500" />}
          title="No Resumes Uploaded Yet"
          description="Upload a PDF or TXT resume to extract skills, evaluate ATS keyword matches, and receive recommendations."
          action={
            <Button size="sm" onClick={() => setIsUploadModalOpen(true)} leftIcon={<Upload className="w-4 h-4" />}>
              Upload Resume
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Resumes & Analysis Form */}
          <div className="space-y-6">
            {/* Resume Selection */}
            <Card title="Your Uploaded Resumes" subtitle="Select a resume to inspect or re-analyze">
              <div className="space-y-2">
                {resumes.map((resume) => {
                  const isSelected = selectedResume?.id === resume.id;
                  const skillsCount = resume.parsed_data?.skills?.length || 0;
                  return (
                    <div
                      key={resume.id}
                      onClick={() => selectResume(resume)}
                      className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50/40 text-primary-900'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <h4 className="text-xs font-semibold truncate">{(resume.original_filename || resume.filename)}</h4>
                        <div className="flex items-center gap-2 text-2xs text-gray-500 mt-0.5">
                          <span>{formatFileSize(resume.file_size)}</span>
                          <span>•</span>
                          <span>{skillsCount} Skills</span>
                          <span>•</span>
                          <span>{formatDate(resume.created_at)}</span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteResume(resume.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                        title="Delete resume"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Analysis Form */}
            {selectedResume && (
              <Card
                title="Run ATS Match Analysis"
                subtitle={`Targeted for "${selectedResume.filename}"`}
              >
                <form onSubmit={handleRunAnalysis} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Target Job Description (Optional)
                    </label>
                    <textarea
                      rows={5}
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste the job description (e.g. required skills, technologies, qualifications)... If left empty, a general evaluation will run."
                      className="w-full p-2.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    isLoading={analyzing}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    Analyze ATS Match
                  </Button>
                </form>
              </Card>
            )}

            {/* Extracted Resume Raw Skills */}
            {selectedResume?.parsed_data?.skills && (
              <Card title="Extracted Resume Skills" subtitle={`${selectedResume.parsed_data.skills.length} recognized skills`}>
                <div className="flex flex-wrap gap-1.5">
                  {selectedResume.parsed_data.skills.map((skill: string, idx: number) => (
                    <Badge key={idx} variant="neutral" size="sm">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Right Column: ATS Scorecard & Recommendations */}
          <div className="lg:col-span-2 space-y-6">
            {analysisError && <Alert type="error" message={analysisError} />}

            {activeAnalysis ? (
              <div className="space-y-6">
                {/* Scorecard Hero */}
                <Card>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={getScoreBadge(((activeAnalysis.match_score ?? activeAnalysis.score) || 0)).variant} size="md">
                          {getScoreBadge(((activeAnalysis.match_score ?? activeAnalysis.score) || 0)).label}
                        </Badge>
                        <span className="text-2xs text-gray-400">Analysis #{activeAnalysis.id}</span>
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">
                        {(activeAnalysis.target_role || 'General Role Alignment') || 'General Role Alignment'}
                      </h2>
                      <p className="text-xs text-gray-500 max-w-lg">
                        Benchmark results evaluated against role requirements and industry standards.
                      </p>
                    </div>

                    {/* Circular Score Gauge */}
                    <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-2xl border border-gray-100 shrink-0">
                      <div className="text-3xl font-extrabold text-primary-700">
                        {Math.round(((activeAnalysis.match_score ?? activeAnalysis.score) || 0))}%
                      </div>
                      <span className="text-2xs font-semibold text-gray-500 uppercase tracking-wider mt-1">
                        ATS Score
                      </span>
                    </div>
                  </div>

                  {/* Score Progress Bar */}
                  <div className="mt-6">
                    <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-500 ${
                          ((activeAnalysis.match_score ?? activeAnalysis.score) || 0) >= 80
                            ? 'bg-green-600'
                            : ((activeAnalysis.match_score ?? activeAnalysis.score) || 0) >= 60
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(5, ((activeAnalysis.match_score ?? activeAnalysis.score) || 0)))}%` }}
                      />
                    </div>
                  </div>
                </Card>

                {/* Skills Breakdown Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Matched Skills */}
                  <Card
                    title={
                      <div className="flex items-center gap-2 text-green-700">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Matched Skills ({activeAnalysis.matched_skills?.length || 0})</span>
                      </div>
                    }
                  >
                    {activeAnalysis.matched_skills && activeAnalysis.matched_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {activeAnalysis.matched_skills.map((skill, i) => (
                          <Badge key={i} variant="success" size="sm">
                            ✓ {skill}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No direct keyword matches found.</p>
                    )}
                  </Card>

                  {/* Missing Skills */}
                  <Card
                    title={
                      <div className="flex items-center gap-2 text-amber-700">
                        <AlertCircle className="w-4 h-4" />
                        <span>Missing Target Skills ({activeAnalysis.missing_skills?.length || 0})</span>
                      </div>
                    }
                  >
                    {activeAnalysis.missing_skills && activeAnalysis.missing_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {activeAnalysis.missing_skills.map((skill, i) => (
                          <Badge key={i} variant="warning" size="sm">
                            + {skill}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No missing skills detected!</p>
                    )}
                  </Card>
                </div>

                {/* Actionable Recommendations */}
                {activeAnalysis.recommendations && activeAnalysis.recommendations.length > 0 && (
                  <Card
                    title="Actionable ATS Recommendations"
                    subtitle="Steps to improve resume match rate and recruiter visibility"
                  >
                    <ul className="space-y-2.5">
                      {activeAnalysis.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700">
                          <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-2xs shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <span className="leading-relaxed">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
              </div>
            ) : (
              <Card>
                <div className="text-center py-16">
                  <Sparkles className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <h3 className="text-sm font-semibold text-gray-800">Ready for Analysis</h3>
                  <p className="text-xs text-gray-500 max-w-sm mx-auto mt-1 mb-4">
                    Paste a target job description or click "Analyze ATS Match" to evaluate this resume.
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => !uploading && setIsUploadModalOpen(false)}
        title="Upload Resume"
        description="Upload your resume in PDF or TXT format for parsing and ATS benchmarking."
        maxWidth="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsUploadModalOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUploadResume} isLoading={uploading} disabled={!uploadFile}>
              Upload & Parse
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {uploadError && <Alert type="error" message={uploadError} />}

          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
              uploadFile ? 'border-primary-500 bg-primary-50/20' : 'border-gray-300 hover:border-primary-400 bg-gray-50/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setUploadFile(e.target.files[0]);
                  setUploadError(null);
                }
              }}
              accept=".pdf,.txt"
              className="hidden"
            />
            <div className="w-10 h-10 rounded-full bg-white shadow-xs mx-auto flex items-center justify-center text-primary-600 mb-2">
              <Upload className="w-5 h-5" />
            </div>
            {uploadFile ? (
              <div>
                <p className="text-sm font-semibold text-gray-900">{uploadFile.name}</p>
                <p className="text-xs text-gray-500 mt-1">{formatFileSize(uploadFile.size)}</p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Click or drag resume file here (.pdf or .txt)
                </p>
                <p className="text-xs text-gray-400 mt-1">Maximum file size 10MB</p>
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};
