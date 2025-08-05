/**
 * Auth Service Tests
 * Testing /services/api/auth.js functionality
 */

import { signup, login, logout, fetchUserRole } from '../auth';
import api from '../../core/axiosClient';

// Mock the apiClient
jest.mock('../../core/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('Auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('signup', () => {
    it('should call API with correct endpoint and data', async () => {
      const mockUserData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        role: 'student'
      };

      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student',
          message: 'User created successfully'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const result = await signup(mockUserData);

      expect(api.post).toHaveBeenCalledWith('register/', mockUserData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle signup errors', async () => {
      const mockUserData = {
        username: 'existinguser',
        email: 'existing@example.com',
        password: 'password123'
      };

      const mockError = {
        response: {
          status: 400,
          data: { error: 'User already exists' }
        }
      };

      api.post.mockRejectedValue(mockError);

      await expect(signup(mockUserData)).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('register/', mockUserData);
    });
  });

  describe('login', () => {
    it('should call API with correct endpoint and credentials', async () => {
      const mockCredentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      const mockResponse = {
        data: {
          access_token: 'jwt-access-token',
          refresh_token: 'jwt-refresh-token',
          user: {
            id: 1,
            email: 'test@example.com',
            role: 'student'
          }
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const result = await login(mockCredentials);

      expect(api.post).toHaveBeenCalledWith('login/', mockCredentials);
      expect(result).toEqual(mockResponse);
    });

    it('should handle login errors with invalid credentials', async () => {
      const mockCredentials = {
        email: 'wrong@example.com',
        password: 'wrongpassword'
      };

      const mockError = {
        response: {
          status: 401,
          data: { error: 'Invalid credentials' }
        }
      };

      api.post.mockRejectedValue(mockError);

      await expect(login(mockCredentials)).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('login/', mockCredentials);
    });

    it('should handle server errors during login', async () => {
      const mockCredentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' }
        }
      };

      api.post.mockRejectedValue(mockError);

      await expect(login(mockCredentials)).rejects.toEqual(mockError);
    });
  });

  describe('logout', () => {
    it('should call logout endpoint without data', async () => {
      const mockResponse = {
        data: { message: 'Logout successful' }
      };

      api.post.mockResolvedValue(mockResponse);

      const result = await logout();

      expect(api.post).toHaveBeenCalledWith('logout/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle logout errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Logout failed' }
        }
      };

      api.post.mockRejectedValue(mockError);

      await expect(logout()).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('logout/');
    });
  });

  describe('fetchUserRole', () => {
    it('should fetch user profile and return role', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'teacher',
          first_name: 'Test',
          last_name: 'User'
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchUserRole();

      expect(api.get).toHaveBeenCalledWith('profile/');
      expect(result).toBe('teacher');
    });

    it('should handle different user roles', async () => {
      const roles = ['student', 'teacher', 'admin'];

      for (const role of roles) {
        api.get.mockResolvedValue({
          data: { id: 1, role }
        });

        const result = await fetchUserRole();
        expect(result).toBe(role);
      }
    });

    it('should handle profile fetch errors', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { error: 'Forbidden' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(fetchUserRole()).rejects.toEqual(mockError);
      expect(api.get).toHaveBeenCalledWith('profile/');
    });

    it('should handle missing role in response', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com'
          // Missing role field
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchUserRole();

      expect(result).toBeUndefined();
    });
  });
});
