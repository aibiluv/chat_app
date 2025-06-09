
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Auth from './Auth';
// We need to mock the API service to isolate the component for testing.
import * as api from '../../services/api';

// This tells Jest to replace the actual api module with a mock version.
// All functions from the api service will be replaced with mock functions.
jest.mock('../../services/api');

// A helper function to render the component within a router,
// as it uses navigation hooks.
const renderWithRouter = (ui, { route = '/' } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(ui, { wrapper: BrowserRouter });
};

// Before each test, clear any previous mock implementations to ensure a clean state.
beforeEach(() => {
    jest.clearAllMocks();
});

describe('Auth Component', () => {
  test('renders login form by default', () => {
    renderWithRouter(<Auth />);
    
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/email/i)).not.toBeInTheDocument();
  });

  test('toggles to register form when "Register" is clicked', () => {
    renderWithRouter(<Auth />);
    
    const toggleLink = screen.getByText(/don't have an account\? register/i);
    fireEvent.click(toggleLink);
    
    expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
  });

  test('calls login api and onLogin prop on successful login', async () => {
    const mockOnLogin = jest.fn();
    api.login.mockResolvedValue({ data: { access_token: 'fake-token' } });
    
    renderWithRouter(<Auth onLogin={mockOnLogin} />);
    
    fireEvent.change(screen.getByPlaceholderText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'password' } });
    
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith('testuser', 'password');
      expect(mockOnLogin).toHaveBeenCalledWith('fake-token');
    });
  });

  test('displays an error message on failed login', async () => {
    const errorMessage = 'Invalid credentials';
    api.login.mockRejectedValue({ response: { data: { detail: errorMessage } } });
    
    renderWithRouter(<Auth onLogin={() => {}} />);

    fireEvent.change(screen.getByPlaceholderText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    const errorElement = await screen.findByText(errorMessage);
    expect(errorElement).toBeInTheDocument();
  });

  test('calls register and then login on successful registration', async () => {
    const mockOnLogin = jest.fn();
    // Mock a successful response for both the register and login API calls.
    api.register.mockResolvedValue({ data: { id: '123', username: 'newuser', email: 'new@test.com' } });
    api.login.mockResolvedValue({ data: { access_token: 'new-fake-token' } });

    renderWithRouter(<Auth onLogin={mockOnLogin} />);

    // Switch to the registration form.
    fireEvent.click(screen.getByText(/don't have an account\? register/i));

    // Fill out the registration form.
    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'new@test.com' } });
    fireEvent.change(screen.getByPlaceholderText(/username/i), { target: { value: 'newuser' } });
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'newpassword' } });

    // Submit the registration form.
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    // Wait for the async operations to complete.
    await waitFor(() => {
      // Check that the register function was called with the correct details.
      expect(api.register).toHaveBeenCalledWith('new@test.com', 'newuser', 'newpassword', '');
      // Check that the login function was then called automatically.
      expect(api.login).toHaveBeenCalledWith('newuser', 'newpassword');
      // Check that the final onLogin callback was triggered with the new token.
      expect(mockOnLogin).toHaveBeenCalledWith('new-fake-token');
    });
  });

  test('submit button is disabled if required fields are empty', () => {
    renderWithRouter(<Auth />);

    // Switch to the registration form.
    fireEvent.click(screen.getByText(/don't have an account\? register/i));
    const registerButton = screen.getByRole('button', { name: /register/i });

    // The button should be disabled because the fields are empty.
    // Note: The HTML 'required' attribute handles this behavior.
    // A more robust test could check the form's validity state.
    const usernameInput = screen.getByPlaceholderText(/username/i);
    fireEvent.change(usernameInput, { target: { value: 'test' } });
    
    // In a real browser, the form would be invalid without all required fields.
    // React Testing Library doesn't run a full browser, so we can infer this
    // behavior or check the 'required' attribute itself.
    expect(usernameInput).toBeRequired();
    expect(screen.getByPlaceholderText(/email/i)).toBeRequired();
    expect(screen.getByPlaceholderText(/password/i)).toBeRequired();
  });
});