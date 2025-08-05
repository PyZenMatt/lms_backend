// MSW handlers per simulare le API del progetto
import { http, HttpResponse } from 'msw';
import { mockData } from './mockData';

const API_BASE = '/api/v1';

export const handlers = [
  // ============== AUTH ENDPOINTS ==============
  http.post(`${API_BASE}/auth/login/`, () => {
    return HttpResponse.json({
      access: mockData.tokens.access,
      refresh: mockData.tokens.refresh,
      user: mockData.users.student
    });
  }),

  http.post(`${API_BASE}/auth/logout/`, () => {
    return HttpResponse.json({ detail: 'Logout successful' });
  }),

  http.post(`${API_BASE}/auth/register/`, () => {
    return HttpResponse.json({
      user: mockData.users.student,
      message: 'Registration successful'
    });
  }),

  http.post(`${API_BASE}/auth/refresh/`, () => {
    return HttpResponse.json({
      access: mockData.tokens.access
    });
  }),

  // ============== PROFILE ENDPOINTS ==============
  http.get(`${API_BASE}/profile/`, () => {
    return HttpResponse.json(mockData.users.student);
  }),

  http.put(`${API_BASE}/profile/`, () => {
    return HttpResponse.json({
      ...mockData.users.student,
      first_name: 'Updated Name'
    });
  }),

  // ============== DASHBOARD ENDPOINTS ==============
  http.get(`${API_BASE}/dashboard/student/`, () => {
    return HttpResponse.json(mockData.dashboards.student);
  }),

  http.get(`${API_BASE}/dashboard/teacher/`, () => {
    return HttpResponse.json(mockData.dashboards.teacher);
  }),

  // ============== COURSES ENDPOINTS ==============
  http.get(`${API_BASE}/courses/`, () => {
    return HttpResponse.json({
      results: mockData.courses.list,
      count: mockData.courses.list.length,
      next: null,
      previous: null
    });
  }),

  http.get(`${API_BASE}/courses/:id/`, ({ params }) => {
    const course = mockData.courses.list.find(c => c.id === parseInt(params.id));
    return course 
      ? HttpResponse.json(course)
      : HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.post(`${API_BASE}/courses/`, () => {
    return HttpResponse.json({
      ...mockData.courses.list[0],
      id: Date.now(),
      title: 'New Course'
    }, { status: 201 });
  }),

  // ============== EXERCISES ENDPOINTS ==============
  http.get(`${API_BASE}/exercises/submissions/`, () => {
    return HttpResponse.json({
      results: mockData.exercises.submissions,
      count: mockData.exercises.submissions.length
    });
  }),

  http.post(`${API_BASE}/exercises/:id/submit/`, () => {
    return HttpResponse.json({
      id: Date.now(),
      score: 85,
      feedback: 'Good work!',
      submitted_at: new Date().toISOString()
    });
  }),

  // ============== BLOCKCHAIN ENDPOINTS ==============
  http.get(`${API_BASE}/blockchain/balance/`, () => {
    return HttpResponse.json({
      balance: mockData.blockchain.balance,
      address: mockData.blockchain.address
    });
  }),

  http.post(`${API_BASE}/blockchain/purchase/`, () => {
    return HttpResponse.json({
      transaction_hash: mockData.blockchain.transactionHash,
      status: 'pending'
    });
  }),

  // ============== NOTIFICATIONS ENDPOINTS ==============
  http.get(`${API_BASE}/notifications/`, () => {
    return HttpResponse.json({
      results: mockData.notifications.list,
      unread_count: mockData.notifications.unreadCount
    });
  }),

  http.patch(`${API_BASE}/notifications/:id/read/`, () => {
    return HttpResponse.json({ status: 'read' });
  }),

  // ============== CHAT ENDPOINTS ==============
  http.get(`${API_BASE}/chat/messages/`, () => {
    return HttpResponse.json({
      results: mockData.chat.messages
    });
  }),

  http.post(`${API_BASE}/chat/messages/`, () => {
    return HttpResponse.json({
      id: Date.now(),
      content: 'Test message',
      sender: mockData.users.student,
      timestamp: new Date().toISOString()
    });
  }),

  // ============== ERROR HANDLERS ==============
  http.get(`${API_BASE}/error/404`, () => {
    return HttpResponse.json(
      { detail: 'Not found' }, 
      { status: 404 }
    );
  }),

  http.get(`${API_BASE}/error/500`, () => {
    return HttpResponse.json(
      { detail: 'Internal server error' }, 
      { status: 500 }
    );
  }),

  // ============== FALLBACK HANDLER ==============
  http.all('*', ({ request }) => {
    console.warn(`Unhandled ${request.method} request to ${request.url}`);
    return HttpResponse.json(
      { detail: 'Mock not implemented' },
      { status: 404 }
    );
  })
];
