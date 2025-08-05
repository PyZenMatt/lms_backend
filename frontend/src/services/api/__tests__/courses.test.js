/**
 * Courses Service Tests
 * Testing /services/api/courses.js functionality
 */

import {
  fetchCourses,
  purchaseCourse,
  createCourse,
  createLesson,
  fetchLessonsForCourse,
  createExercise,
  fetchExercisesForLesson,
  fetchCourseDetail,
  fetchLessonDetail,
  fetchExerciseDetail
} from '../courses';
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

describe('Courses Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchCourses', () => {
    it('should fetch courses without parameters', async () => {
      const mockResponse = {
        data: {
          results: [
            { id: 1, title: 'React Basics', category: 'programming' },
            { id: 2, title: 'Node.js Advanced', category: 'programming' }
          ]
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await fetchCourses();

      expect(api.get).toHaveBeenCalledWith('courses/');
      expect(result).toEqual(mockResponse);
    });

    it('should fetch courses with category filter', async () => {
      const mockResponse = {
        data: {
          results: [
            { id: 1, title: 'React Basics', category: 'programming' }
          ]
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = { category: 'programming' };
      const result = await fetchCourses(params);

      expect(api.get).toHaveBeenCalledWith('courses/?category=programming');
      expect(result).toEqual(mockResponse);
    });

    it('should fetch courses with search parameter', async () => {
      const mockResponse = {
        data: {
          results: [
            { id: 1, title: 'React Basics', category: 'programming' }
          ]
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = { search: 'React' };
      const result = await fetchCourses(params);

      expect(api.get).toHaveBeenCalledWith('courses/?search=React');
      expect(result).toEqual(mockResponse);
    });

    it('should fetch courses with multiple parameters', async () => {
      const mockResponse = {
        data: {
          results: [
            { id: 1, title: 'Advanced React', category: 'programming' }
          ]
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = {
        category: 'programming',
        search: 'React',
        ordering: '-created_at'
      };
      const result = await fetchCourses(params);

      expect(api.get).toHaveBeenCalledWith('courses/?category=programming&search=React&ordering=-created_at');
      expect(result).toEqual(mockResponse);
    });

    it('should ignore "all" category filter', async () => {
      const mockResponse = { data: { results: [] } };
      api.get.mockResolvedValue(mockResponse);

      const params = { category: 'all' };
      await fetchCourses(params);

      expect(api.get).toHaveBeenCalledWith('courses/');
    });
  });

  describe('purchaseCourse', () => {
    it('should purchase course with wallet address', async () => {
      const mockResponse = {
        data: {
          id: 1,
          course_id: 123,
          wallet_address: '0x123...',
          transaction_hash: '0xabc...',
          status: 'completed'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const courseId = 123;
      const walletAddress = '0x123...';
      const result = await purchaseCourse(courseId, walletAddress);

      expect(api.post).toHaveBeenCalledWith('courses/123/purchase/', {
        wallet_address: walletAddress
      });
      expect(result).toEqual(mockResponse);
    });

    it('should purchase course with additional transaction data', async () => {
      const mockResponse = {
        data: { id: 1, status: 'completed' }
      };

      api.post.mockResolvedValue(mockResponse);

      const courseId = 123;
      const walletAddress = '0x123...';
      const transactionData = {
        transaction_hash: '0xabc...',
        amount: '0.1',
        currency: 'ETH'
      };

      await purchaseCourse(courseId, walletAddress, transactionData);

      expect(api.post).toHaveBeenCalledWith('courses/123/purchase/', {
        wallet_address: walletAddress,
        transaction_hash: '0xabc...',
        amount: '0.1',
        currency: 'ETH'
      });
    });

    it('should handle purchase errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Insufficient funds' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const courseId = 123;
      const walletAddress = '0x123...';

      await expect(purchaseCourse(courseId, walletAddress)).rejects.toEqual(mockError);
    });
  });

  describe('createCourse', () => {
    it('should create course with regular data', async () => {
      const mockResponse = {
        data: {
          id: 1,
          title: 'New Course',
          description: 'Course description',
          price: '0.1'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const courseData = {
        title: 'New Course',
        description: 'Course description',
        price: '0.1'
      };

      const result = await createCourse(courseData);

      expect(api.post).toHaveBeenCalledWith('courses/', courseData, {});
      expect(result).toEqual(mockResponse);
    });

    it('should create course with FormData', async () => {
      const mockResponse = {
        data: { id: 1, title: 'New Course' }
      };

      api.post.mockResolvedValue(mockResponse);

      const formData = new FormData();
      formData.append('title', 'New Course');
      formData.append('file', new Blob(['content']));

      const result = await createCourse(formData);

      expect(api.post).toHaveBeenCalledWith('courses/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createLesson', () => {
    it('should create lesson with regular data', async () => {
      const mockResponse = {
        data: {
          id: 1,
          title: 'New Lesson',
          course: 123
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const lessonData = {
        title: 'New Lesson',
        course: 123,
        content: 'Lesson content'
      };

      const result = await createLesson(lessonData);

      expect(api.post).toHaveBeenCalledWith('lessons/create/', lessonData, {});
      expect(result).toEqual(mockResponse);
    });

    it('should create lesson with FormData', async () => {
      const mockResponse = {
        data: { id: 1, title: 'New Lesson' }
      };

      api.post.mockResolvedValue(mockResponse);

      const formData = new FormData();
      formData.append('title', 'New Lesson');
      formData.append('video', new Blob(['video content']));

      const result = await createLesson(formData);

      expect(api.post).toHaveBeenCalledWith('lessons/create/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('fetchLessonsForCourse', () => {
    it('should fetch lessons for a specific course', async () => {
      const mockResponse = {
        data: [
          { id: 1, title: 'Lesson 1', course: 123 },
          { id: 2, title: 'Lesson 2', course: 123 }
        ]
      };

      api.get.mockResolvedValue(mockResponse);

      const courseId = 123;
      const result = await fetchLessonsForCourse(courseId);

      expect(api.get).toHaveBeenCalledWith('courses/123/lessons/');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createExercise', () => {
    it('should create exercise with regular data', async () => {
      const mockResponse = {
        data: {
          id: 1,
          title: 'New Exercise',
          lesson: 456
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const exerciseData = {
        title: 'New Exercise',
        description: 'Exercise description',
        lesson: 456
      };

      const result = await createExercise(exerciseData);

      expect(api.post).toHaveBeenCalledWith('exercises/create/', exerciseData, {});
      expect(result).toEqual(mockResponse);
    });
  });

  describe('fetchExercisesForLesson', () => {
    it('should fetch exercises for a specific lesson', async () => {
      const mockResponse = {
        data: [
          { id: 1, title: 'Exercise 1', lesson: 456 },
          { id: 2, title: 'Exercise 2', lesson: 456 }
        ]
      };

      api.get.mockResolvedValue(mockResponse);

      const lessonId = 456;
      const result = await fetchExercisesForLesson(lessonId);

      expect(api.get).toHaveBeenCalledWith('lessons/456/exercises/');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('fetchCourseDetail', () => {
    it('should fetch course details and return data', async () => {
      const mockResponse = {
        data: {
          id: 123,
          title: 'Course Title',
          description: 'Course description',
          lessons: []
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const courseId = 123;
      const result = await fetchCourseDetail(courseId);

      expect(api.get).toHaveBeenCalledWith('courses/123/');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('fetchLessonDetail', () => {
    it('should fetch lesson details and return data', async () => {
      const mockResponse = {
        data: {
          id: 456,
          title: 'Lesson Title',
          content: 'Lesson content',
          course: 123
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const lessonId = 456;
      const result = await fetchLessonDetail(lessonId);

      expect(api.get).toHaveBeenCalledWith('lessons/456/');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('fetchExerciseDetail', () => {
    it('should fetch exercise details and return data', async () => {
      const mockResponse = {
        data: {
          id: 789,
          title: 'Exercise Title',
          description: 'Exercise description',
          lesson: 456
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const exerciseId = 789;
      const result = await fetchExerciseDetail(exerciseId);

      expect(api.get).toHaveBeenCalledWith('exercises/789/');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('error handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      api.get.mockRejectedValue(networkError);

      await expect(fetchCourses()).rejects.toThrow('Network Error');
    });

    it('should handle 404 errors for course details', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { error: 'Course not found' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(fetchCourseDetail(999)).rejects.toEqual(mockError);
    });
  });
});
