import { apiGet } from '../utils/apiHelpers';

/**
 * Enhanced batch API service that leverages the new backend batch endpoints
 * These endpoints return combined data in a single request, reducing load times
 */

// Batch endpoint for student dashboard data
export const fetchStudentBatchData = async () => {
  try {
    const data = await apiGet('/batch/student-data/');
    return {
      courses: data.courses || [],
      progress: data.progress || {},
      notifications: data.notifications || [],
      recent_activity: data.recent_activity || [],
      recent_transactions: data.recent_transactions || []
    };
  } catch (error) {
    console.error('Error fetching student batch data:', error);
    throw error;
  }
};

// Batch endpoint for course data with lessons and progress
export const fetchCourseBatchData = async (courseId) => {
  try {
    const data = await apiGet(`/batch/course-data/${courseId}/`);
    return {
      course: data.course || {},
      lessons: data.lessons || [],
      progress: data.progress || {},
      exercises: data.exercises || [],
      completed_lessons: data.completed_lessons || []
    };
  } catch (error) {
    console.error('Error fetching course batch data:', error);
    throw error;
  }
};

// Batch endpoint for lesson data with exercises and completion status
export const fetchLessonBatchData = async (lessonId) => {
  try {
    const data = await apiGet(`/batch/lesson-data/${lessonId}/`);
    return {
      lesson: data.lesson || {},
      exercises: data.exercises || [],
      completion_status: data.completion_status || false,
      course_info: data.course_info || {},
      progress_data: data.progress_data || {}
    };
  } catch (error) {
    console.error('Error fetching lesson batch data:', error);
    throw error;
  }
};

// Teacher batch endpoint for dashboard data
export const fetchTeacherBatchData = async () => {
  try {
    const data = await apiGet('/batch/teacher-data/');
    return {
      courses: data.courses || [],
      sales: data.sales || { daily: 0, monthly: 0, yearly: 0 },
      transactions: data.transactions || [],
      student_stats: data.student_stats || {},
      revenue_stats: data.revenue_stats || {}
    };
  } catch (error) {
    console.error('Error fetching teacher batch data:', error);
    throw error;
  }
};

// Utility function to batch multiple API calls
export const batchApiCalls = async (calls, { maxRetries = 3, retryDelay = 1000 } = {}) => {
  const results = [];
  
  for (const call of calls) {
    let attempts = 0;
    let success = false;
    
    while (!success && attempts < maxRetries) {
      try {
        const result = await call();
        results.push({ success: true, data: result });
        success = true;
      } catch (error) {
        attempts++;
        if (attempts < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        } else {
          results.push({ success: false, error });
        }
      }
    }
  }
  
  return results;
};

// Enhanced error handling for batch requests
export const handleBatchError = (error, fallbackData = {}) => {
  console.error('Batch API error:', error);
  
  // Return fallback data with loading states
  return {
    loading: false,
    error: error.message || 'Errore nel caricamento dei dati',
    data: fallbackData
  };
};
