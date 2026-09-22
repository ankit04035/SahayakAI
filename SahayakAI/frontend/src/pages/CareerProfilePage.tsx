import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  Save,
  CheckCircle2,
  AlertCircle,
  Plus,
  X,
  Compass,
  ArrowRight,
  Briefcase,
  Target,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getCareerProfile, upsertCareerProfile } from '../api/career';
import { CareerProfileRead } from '../types/career';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

const CURATED_ROLES = [
  'Software Engineer',
  'Data Scientist',
  'Machine Learning Engineer',
  'Cloud Solutions Architect',
  'DevOps Engineer',
  'Cybersecurity Analyst',
  'Full Stack Developer',
  'Product Manager',
  'AI Research Scientist',
  'Data Engineer',
];

export const CareerProfilePage: React.FC = () => {
  const { userId } = useUser();
  const [profile, setProfile] = useState<CareerProfileRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form fields
  const [targetRole, setTargetRole] = useState(CURATED_ROLES[0]);
  const [isCustomRole, setIsCustomRole] = useState(false);
  const [customRoleInput, setCustomRoleInput] = useState('');
  const [degree, setDegree] = useState('');
  const [experience, setExperience] = useState('Beginner');
  const [currentSkills, setCurrentSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [interestInput, setInterestInput] = useState('');

  useEffect(() => {
    let isMounted = true;
    const loadProfile = async () => {
      setLoading(true);
      try {
        const data = await getCareerProfile(userId);
        if (isMounted && data) {
          setProfile(data);
          if (CURATED_ROLES.includes(data.target_role)) {
            setTargetRole(data.target_role);
            setIsCustomRole(false);
          } else {
            setIsCustomRole(true);
            setCustomRoleInput(data.target_role);
          }
          setDegree(data.degree || '');
          setExperience(data.experience || 'Beginner');
          setCurrentSkills(data.current_skills || []);
          setInterests(data.interests || []);
        }
      } catch {
        // No existing profile
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadProfile();
    return () => {
      isMounted = false;
    };
  }, [userId]);

  const handleAddSkill = () => {
    const trimmed = skillInput.trim();
    if (trimmed && !currentSkills.includes(trimmed)) {
      setCurrentSkills([...currentSkills, trimmed]);
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setCurrentSkills(currentSkills.filter((s) => s !== skill));
  };

  const handleAddInterest = () => {
    const trimmed = interestInput.trim();
    if (trimmed && !interests.includes(trimmed)) {
      setInterests([...interests, trimmed]);
      setInterestInput('');
    }
  };

  const handleRemoveInterest = (item: string) => {
    setInterests(interests.filter((i) => i !== item));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalRole = isCustomRole ? customRoleInput.trim() : targetRole;
    if (!finalRole) {
      setStatusMessage({ type: 'error', text: 'Target role is required.' });
      return;
    }

    setSaving(true);
    setStatusMessage(null);
    try {
      const res = await upsertCareerProfile(
        {
          target_role: finalRole,
          degree: degree.trim() || undefined,
          current_skills: currentSkills,
          experience: experience.trim() || undefined,
          interests: interests,
        },
        userId
      );
      setProfile(res);
      setStatusMessage({ type: 'success', text: 'Career profile updated successfully!' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to save profile' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <LoadingSpinner size="lg" label="Loading career profile..." />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Career Profile</h1>
          <p className="text-sm text-gray-500 mt-1">
            Define your degree, aspirations, technical skills, and target discipline to generate 12-week roadmaps.
          </p>
        </div>
        <Link to="/career/roadmap">
          <Button variant="outline" rightIcon={<ArrowRight className="w-4 h-4" />}>
            View Roadmaps
          </Button>
        </Link>
      </div>

      {statusMessage && (
        <Alert
          type={statusMessage.type}
          message={statusMessage.text}
          onClose={() => setStatusMessage(null)}
        />
      )}

      {/* Main Profile Form */}
      <Card>
        <form onSubmit={handleSave} className="space-y-6">
          {/* Target Role */}
          <div>
            <label className="block text-xs font-bold text-gray-900 uppercase tracking-wider mb-2">
              Target Career Role / Discipline *
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <select
                value={isCustomRole ? 'CUSTOM' : targetRole}
                onChange={(e) => {
                  if (e.target.value === 'CUSTOM') {
                    setIsCustomRole(true);
                  } else {
                    setIsCustomRole(false);
                    setTargetRole(e.target.value);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {CURATED_ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
                <option value="CUSTOM">Custom Target Role...</option>
              </select>

              {isCustomRole && (
                <input
                  type="text"
                  placeholder="Enter custom target role"
                  value={customRoleInput}
                  onChange={(e) => setCustomRoleInput(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              )}
            </div>
          </div>

          {/* Degree & Experience */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Degree / Field of Study
              </label>
              <input
                type="text"
                placeholder="e.g. B.Tech Computer Science, BCA, MS AI"
                value={degree}
                onChange={(e) => setDegree(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Experience Level
              </label>
              <select
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="Beginner / Student">Beginner / Student</option>
                <option value="Intermediate / 1-2 Yrs">Intermediate / 1-2 Yrs</option>
                <option value="Experienced / 3+ Yrs">Experienced / 3+ Yrs</option>
              </select>
            </div>
          </div>

          {/* Current Skills Tag Input */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Current Technical Skills
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Add a skill (e.g. Python, Docker, React, PostgreSQL)..."
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <Button type="button" variant="secondary" onClick={handleAddSkill}>
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-1.5 min-h-8 p-2 bg-gray-50 rounded-lg border border-gray-200">
              {currentSkills.length === 0 ? (
                <span className="text-2xs text-gray-400">No skills added yet.</span>
              ) : (
                currentSkills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-gray-200 rounded-full text-xs font-medium text-gray-700 shadow-2xs"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Interests Tag Input */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Interests & Focus Areas
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Add an interest (e.g. Generative AI, Cloud Native, Cybersecurity)..."
                value={interestInput}
                onChange={(e) => setInterestInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddInterest();
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <Button type="button" variant="secondary" onClick={handleAddInterest}>
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-1.5 min-h-8 p-2 bg-gray-50 rounded-lg border border-gray-200">
              {interests.length === 0 ? (
                <span className="text-2xs text-gray-400">No interests added yet.</span>
              ) : (
                interests.map((interest) => (
                  <span
                    key={interest}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-gray-200 rounded-full text-xs font-medium text-gray-700 shadow-2xs"
                  >
                    {interest}
                    <button
                      type="button"
                      onClick={() => handleRemoveInterest(interest)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Submit */}
          <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
            <span className="text-2xs text-gray-400">Scoped to Dev User #{userId}</span>
            <Button type="submit" isLoading={saving} leftIcon={<Save className="w-4 h-4" />}>
              Save Profile
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
