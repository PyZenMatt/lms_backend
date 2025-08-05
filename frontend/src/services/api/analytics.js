import apiClient from '../core/axiosClient';

/**
 * Analytics API service for revenue and platform metrics
 */

// Get comprehensive analytics dashboard data
export const getAnalyticsData = async () => {
  return await apiClient.get('/analytics/dashboard/');
};

// Get revenue chart data for the last 30 days
export const getRevenueChartData = async () => {
  return await apiClient.get('/analytics/revenue-chart/');
};

// Get platform public statistics
export const getPublicStats = async () => {
  return await apiClient.get('/analytics/public-stats/');
};

// Get real-time metrics for live dashboard updates
export const getLiveMetrics = async () => {
  return await apiClient.get('/core/analytics/live-metrics/');
};

export default {
  getAnalyticsData,
  getRevenueChartData,
  getPublicStats,
  getLiveMetrics
};
