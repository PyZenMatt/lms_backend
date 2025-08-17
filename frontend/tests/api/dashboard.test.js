/**
 * Dashboard Service Tests
 * Testing /services/api/dashboard.js functionality
 */

import {
  fetchUserProfile,
  fetchStudentDashboard,
  fetchTeacherDashboard,
  fetchStudentSubmissions,
  updateUserProfile,
  connectWallet,
  disconnectWallet
} from '../../src/services/api/dashboard';
import api from '../../src/services/core/axiosClient';

// Mock the apiClient
vi.mock('../../core/apiClient', () => ({
  __esModule: true,
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  delete: vi.fn()
  },
}));

describe('Dashboard Service', () => {
  beforeEach(() => {
  vi.clearAllMocks();
  });

  describe('fetchUserProfile', () => {
    it('should fetch user profile data', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student',
          first_name: 'Test',
          last_name: 'User',
          wallet_address: '0x123...'
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchUserProfile();

      expect(api.get).toHaveBeenCalledWith('profile/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle profile fetch errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(fetchUserProfile()).rejects.toEqual(mockError);
      expect(api.get).toHaveBeenCalledWith('profile/');
    });
  });

  describe('fetchStudentDashboard', () => {
    it('should fetch student dashboard data', async () => {
      const mockResponse = {
        data: {
          purchased_courses: [
            { id: 1, title: 'React Basics', progress: 50 },
            { id: 2, title: 'Node.js', progress: 25 }
          ],
          wallet_balance: '1.5',
          recent_activities: [],
          statistics: {
            total_courses: 2,
            completed_courses: 0,
            in_progress_courses: 2
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchStudentDashboard();

      expect(api.get).toHaveBeenCalledWith('dashboard/student/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle student dashboard errors', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { error: 'Access denied - not a student' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(fetchStudentDashboard()).rejects.toEqual(mockError);
    });
  });

  describe('fetchTeacherDashboard', () => {
    it('should fetch teacher dashboard data', async () => {
      const mockResponse = {
        data: {
          created_courses: [
            { id: 1, title: 'React Advanced', students: 25, revenue: '2.5' },
            { id: 2, title: 'JavaScript Fundamentals', students: 50, revenue: '5.0' }
          ],
          total_revenue: '7.5',
          total_students: 75,
          statistics: {
            courses_created: 2,
            total_enrollments: 75,
            monthly_revenue: '2.0'
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchTeacherDashboard();

      expect(api.get).toHaveBeenCalledWith('dashboard/teacher/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle teacher dashboard errors', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { error: 'Access denied - not a teacher' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(fetchTeacherDashboard()).rejects.toEqual(mockError);
    });
  });

  describe('fetchStudentSubmissions', () => {
    it('should fetch student exercise submissions', async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            exercise: { id: 10, title: 'React Components' },
            submitted_at: '2025-06-21T10:00:00Z',
            grade: 85,
            status: 'graded'
          },
          {
            id: 2,
            exercise: { id: 11, title: 'State Management' },
            submitted_at: '2025-06-20T15:30:00Z',
            grade: null,
            status: 'pending'
          }
        ]
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchStudentSubmissions();

      expect(api.get).toHaveBeenCalledWith('exercises/submissions/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle empty submissions', async () => {
      const mockResponse = { data: [] };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchStudentSubmissions();

      expect(result.data).toEqual([]);
    });
  });

  describe('updateUserProfile', () => {
    it('should update profile with regular data', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'updateduser',
          email: 'updated@example.com',
          first_name: 'Updated',
          last_name: 'User'
        }
      };

      api.put.mockResolvedValue(mockResponse);

      const updateData = {
        first_name: 'Updated',
        last_name: 'User',
        email: 'updated@example.com'
      };

      const result = await updateUserProfile(updateData);

      expect(api.put).toHaveBeenCalledWith('profile/', updateData, {});
      expect(result).toEqual(mockResponse);
    });

    it('should update profile with FormData (file upload)', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          profile_picture: '/media/profiles/picture.jpg'
        }
      };

      api.put.mockResolvedValue(mockResponse);

      const formData = new FormData();
      formData.append('first_name', 'Test');
      formData.append('profile_picture', new Blob(['image data']));

      const result = await updateUserProfile(formData);

      expect(api.put).toHaveBeenCalledWith('profile/', formData, {
        transformRequest: expect.any(Array)
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle profile update errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { email: ['This email is already taken'] }
        }
      };

      api.put.mockRejectedValue(mockError);

      const updateData = { email: 'taken@example.com' };

      await expect(updateUserProfile(updateData)).rejects.toEqual(mockError);
    });
  });

  describe('connectWallet', () => {
    it('should connect wallet with valid address', async () => {
      const mockResponse = {
        data: {
          wallet_address: '0x123456789abcdef',
          connected: true,
          balance: '1.25'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const walletAddress = '0x123456789abcdef';
      const result = await connectWallet(walletAddress);

      expect(api.post).toHaveBeenCalledWith('wallet/connect/', {
        wallet_address: walletAddress
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle wallet connection errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid wallet address' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const invalidAddress = 'invalid-address';

      await expect(connectWallet(invalidAddress)).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('wallet/connect/', {
        wallet_address: invalidAddress
      });
    });

    it('should handle wallet already connected error', async () => {
      const mockError = {
        response: {
          status: 409,
          data: { error: 'Wallet already connected' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const walletAddress = '0x123456789abcdef';

      await expect(connectWallet(walletAddress)).rejects.toEqual(mockError);
    });
  });

  describe('disconnectWallet', () => {
    it('should disconnect wallet successfully', async () => {
      const mockResponse = {
        data: {
          message: 'Wallet disconnected successfully',
          connected: false
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const result = await disconnectWallet();

      expect(api.post).toHaveBeenCalledWith('wallet/disconnect/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle wallet disconnect errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'No wallet connected' }
        }
      };

      api.post.mockRejectedValue(mockError);

      await expect(disconnectWallet()).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('wallet/disconnect/');
    });
  });

  describe('error handling scenarios', () => {
    it('should handle network timeouts', async () => {
      const timeoutError = new Error('timeout of 10000ms exceeded');
      api.get.mockRejectedValue(timeoutError);

      await expect(fetchUserProfile()).rejects.toThrow('timeout of 10000ms exceeded');
    });

    it('should handle server errors', async () => {
      const serverError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' }
        }
      };

      api.get.mockRejectedValue(serverError);

      await expect(fetchStudentDashboard()).rejects.toEqual(serverError);
    });

    it('should handle unauthorized access', async () => {
      const authError = {
        response: {
          status: 401,
          data: { error: 'Token expired' }
        }
      };

      api.get.mockRejectedValue(authError);

      await expect(fetchTeacherDashboard()).rejects.toEqual(authError);
    });
  });
});
