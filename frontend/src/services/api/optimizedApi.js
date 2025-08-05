// Optimized API Service with batch calls and caching
// Uses the batch endpoints created in Django backend

import axios from 'axios';

class OptimizedAPIService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.pendingRequests = new Map();
    
    // Create axios instance with optimizations
    this.api = axios.create({
      baseURL: '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      }
    });

    // Add request interceptor for auth, but skip /login/ and /register/
    this.api.interceptors.request.use((config) => {
      const skipAuth = config.url && (
        config.url.includes('/login') || config.url.includes('/register')
      );
      if (!skipAuth) {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
      return config;
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Cache management
  getCacheKey(url, params) {
    return `${url}?${JSON.stringify(params || {})}`;
  }

  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  // Deduplicate simultaneous requests
  async makeRequest(key, requestFn) {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key);
    }

    const request = requestFn();
    this.pendingRequests.set(key, request);
    
    try {
      const result = await request;
      this.pendingRequests.delete(key);
      return result;
    } catch (error) {
      this.pendingRequests.delete(key);
      throw error;
    }
  }

  // ✅ OPTIMIZED - Student batch data (replaces multiple API calls)
  async getStudentDashboardData() {
    const cacheKey = 'student-batch-data';
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get('/core/api/student/batch-data/');
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // ✅ OPTIMIZED - Course batch data (course + lessons + progress)
  async getCourseBatchData(courseId) {
    const cacheKey = `course-batch-data-${courseId}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get(`/core/api/course/${courseId}/batch-data/`);
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // ✅ OPTIMIZED - Lesson batch data (lesson + exercises + progress)
  async getLessonBatchData(lessonId) {
    const cacheKey = `lesson-batch-data-${lessonId}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get(`/core/api/lesson/${lessonId}/batch-data/`);
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // ✅ OPTIMIZED - Teacher dashboard with single request
  async getTeacherDashboardData() {
    const cacheKey = 'teacher-dashboard-data';
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get('/core/dashboard/teacher/');
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // ✅ OPTIMIZED - Paginated courses with search
  async getCourses(page = 1, search = '', category = '') {
    const cacheKey = `courses-${page}-${search}-${category}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get('/courses/courses/', {
        params: { page, search, category }
      });
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // Notifications with batch loading
  async getNotifications() {
    const cacheKey = 'notifications';
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    return this.makeRequest(cacheKey, async () => {
      const response = await this.api.get('/notifications/');
      this.setCache(cacheKey, response.data);
      return response.data;
    });
  }

  // Update progress with optimistic updates
  async updateProgress(exerciseId, completed) {
    try {
      // Optimistic update - update UI immediately
      const cacheKeys = Array.from(this.cache.keys()).filter(key => 
        key.includes('student-batch') || key.includes('lesson-batch') || key.includes('course-batch')
      );
      
      // Clear related cache
      cacheKeys.forEach(key => this.cache.delete(key));

      const response = await this.api.post(`/courses/exercises/${exerciseId}/complete/`, {
        completed
      });
      
      return response.data;
    } catch (error) {
      // Revert optimistic update on error by clearing cache
      this.clearCache();
      throw error;
    }
  }

  // Authentication
  async login(credentials) {
    const response = await this.api.post('/login/', credentials);
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    return response.data;
  }

  async logout() {
    localStorage.removeItem('token');
    this.clearCache();
    await this.api.post('/logout/');
  }

  // Cache management
  clearCache() {
    this.cache.clear();
    this.pendingRequests.clear();
  }

  clearUserCache() {
    // Clear user-specific cache on data updates
    const userCacheKeys = Array.from(this.cache.keys()).filter(key => 
      key.includes('student-batch') || 
      key.includes('teacher-dashboard') || 
      key.includes('notifications')
    );
    userCacheKeys.forEach(key => this.cache.delete(key));
  }

  // Preload critical data
  async preloadCriticalData() {
    try {
      // Preload user dashboard data
      await this.getStudentDashboardData();
      
      // Preload notifications
      await this.getNotifications();
      
      console.log('✅ Critical data preloaded');
    } catch (error) {
      console.warn('⚠️ Failed to preload critical data:', error);
    }
  }
}

// Create singleton instance
const apiService = new OptimizedAPIService();

export default apiService;
