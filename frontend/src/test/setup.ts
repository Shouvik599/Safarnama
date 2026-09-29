import '@testing-library/jest-dom/vitest';

// Polyfill window.scrollTo if needed in JSDOM
if (typeof window !== 'undefined') {
  window.scrollTo = () => {};
}
