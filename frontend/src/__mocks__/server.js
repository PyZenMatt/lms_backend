// MSW server per intercettare le richieste API durante i test
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup server con tutti gli handlers
export const server = setupServer(...handlers);
