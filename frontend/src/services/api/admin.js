import api from '../core/axiosClient';

export const fetchPendingTeachers = async () => {
  return api.get('pending-teachers/');
};

export const approveTeacher = async (userId) => {
  return api.post(`approve-teacher/${userId}/`);
};

export const rejectTeacher = async (userId) => {
  return api.post(`reject-teacher/${userId}/`);
};

export const fetchAdminDashboard = async () => {
  return api.get('dashboard/admin/');
};

export const fetchPendingCourses = async () => {
  return api.get('pending-courses/');
};

export const approveCourse = async (courseId) => {
  return api.post(`approve-course/${courseId}/`);
};

export const rejectCourse = async (courseId) => {
  return api.post(`reject-course/${courseId}/`);
};

export const fetchApprovalStats = async () => {
  return api.get('admin/approval-stats/');
};
