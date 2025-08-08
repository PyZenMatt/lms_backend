import api from '../core/axiosClient';

export const fetchAssignedReviews = () => api.get('/reviews/assigned/');
export const fetchSubmissionForReview = (submissionId) => api.get(`/exercises/${submissionId}/`);
export const sendReviewScore = (submissionId, payload) => api.post(`/exercises/${submissionId}/review/`, payload);
