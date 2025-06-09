import '@testing-library/jest-dom';

// Mock the jwt-decode library.
// This prevents errors in tests that don't need to test JWT decoding directly.
jest.mock('jwt-decode', () => ({
  __esModule: true,
  default: () => ({ sub: 'testuser', exp: Date.now() / 1000 + 3600 }),
}));