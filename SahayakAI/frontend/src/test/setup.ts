import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// Polyfill localStorage for node 26 jsdom
const storage: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => storage[key] || null,
  setItem: (key: string, val: string) => {
    storage[key] = String(val);
  },
  removeItem: (key: string) => {
    delete storage[key];
  },
  clear: () => {
    for (const key in storage) {
      delete storage[key];
    }
  },
  key: (i: number) => Object.keys(storage)[i] || null,
  get length() {
    return Object.keys(storage).length;
  },
};

Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });
if (typeof globalThis !== 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });
}

// Polyfill window.scrollTo
Object.defineProperty(window, 'scrollTo', { value: () => {}, writable: true });

afterEach(() => {
  cleanup();
});
