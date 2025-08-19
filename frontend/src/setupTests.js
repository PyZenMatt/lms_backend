import '@testing-library/jest-dom';
import { beforeAll, afterAll, vi } from 'vitest';

let errorSpy; let warnSpy;
beforeAll(() => {
	errorSpy = vi.spyOn(console, 'error').mockImplementation((...args) => {
		throw new Error('console.error intercettato: ' + args.join(' '));
	});
	warnSpy = vi.spyOn(console, 'warn').mockImplementation((...args) => {
		throw new Error('console.warn intercettato: ' + args.join(' '));
	});
});
afterAll(() => { errorSpy?.mockRestore(); warnSpy?.mockRestore(); });
