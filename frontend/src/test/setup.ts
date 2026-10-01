import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Polyfill window.scrollTo and window.matchMedia in JSDOM
if (typeof window !== 'undefined') {
  window.scrollTo = () => {};
  window.matchMedia =
    window.matchMedia ||
    function () {
      return {
        matches: false,
        media: '',
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      };
    };

  (window as any).ResizeObserver =
    (window as any).ResizeObserver ||
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
}

vi.mock('ogl', () => {
  return {
    Renderer: class {
      gl = {
        clearColor: () => {},
        enable: () => {},
        blendFunc: () => {},
        canvas: typeof document !== 'undefined' ? document.createElement('canvas') : {},
        getExtension: () => null,
      };
      setSize() {}
      render() {}
    },
    Program: class {
      uniforms = {
        uTime: { value: 0 },
        uResolution: { value: [100, 100] },
        uAmplitude: { value: 0.88 },
        uColorStops: { value: [] },
      };
    },
    Color: class {},
    Mesh: class {},
    Triangle: class {
      attributes = {};
    },
  };
});
