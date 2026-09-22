export function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  if (i === 0) return `${bytes} B`;
  const val = (bytes / Math.pow(k, i)).toFixed(dm);
  return `${val} ${sizes[i]}`;
}
export const formatFileSize = formatBytes;

export function formatDate(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
  }).format(date);
}

export function formatPercent(value?: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${Math.round(value)}%`;
}

export function formatScorePercentage(score: number): string {
  if (score === null || score === undefined) return '0%';
  const clamped = Math.max(0, Math.min(1, score));
  return `${Math.round(clamped * 100)}%`;
}

export function truncate(text: string, length: number = 100): string {
  if (!text) return '';
  if (text.length <= length) return text;
  return `${text.substring(0, length)}...`;
}
export const truncateText = truncate;
