import { describe, it, expect } from 'vitest';
import { formatFileSize, formatScorePercentage, truncateText } from '../utils/formatters';

describe('formatters utility functions', () => {
  it('formats file sizes accurately', () => {
    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize(512)).toBe('512 B');
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1048576)).toBe('1.0 MB');
    expect(formatFileSize(2621440)).toBe('2.5 MB');
  });

  it('formats score percentages with clamp', () => {
    expect(formatScorePercentage(0.854)).toBe('85%');
    expect(formatScorePercentage(1)).toBe('100%');
    expect(formatScorePercentage(0)).toBe('0%');
    expect(formatScorePercentage(-0.2)).toBe('0%');
    expect(formatScorePercentage(1.5)).toBe('100%');
  });

  it('truncates text safely', () => {
    expect(truncateText('short text', 20)).toBe('short text');
    expect(truncateText('this is a longer text that needs truncation', 15)).toBe('this is a longe...');
  });
});
