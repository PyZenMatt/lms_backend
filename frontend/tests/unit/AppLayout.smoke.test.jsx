import { render, screen } from '@testing-library/react';
import AppLayout from '../../src/layouts/AppLayout';

test('renders main layout', () => {
  render(<AppLayout />);
  expect(screen.getByTestId('main-layout')).toBeInTheDocument();
});
