import { render, screen, fireEvent } from '@testing-library/react';
import SignInForm from '../../src/views/auth/signin/SignIn1_new.jsx';

test('sign-in form submits with valid data', async () => {
  render(<SignInForm />);
  fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'test@test.com' } });
  fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
  fireEvent.click(screen.getByRole('button', { name: /Accedi/i }));
  expect(await screen.findByText(/Dashboard/i)).toBeInTheDocument();
});
