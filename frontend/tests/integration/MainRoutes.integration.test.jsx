import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AppRoutes from '../../src/routes';

test('renders dashboard route', async () => {
  render(
    <MemoryRouter initialEntries={['/dashboard/student']}>
      <AppRoutes />
    </MemoryRouter>
  );
  expect(await screen.findByText(/Benvenuto/i)).toBeInTheDocument();
});
