import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import UnifiedTeacherNotifications from '../UnifiedTeacherNotifications';
import axiosClient from '../../../services/core/axiosClient';

// Mock axios client used by the component
jest.mock('../../../services/core/axiosClient', () => {
  const mock = {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } }
  };
  return { __esModule: true, default: mock };
});

describe('UnifiedTeacherNotifications', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  jest.spyOn(global, 'setInterval').mockImplementation(() => {
      // Don't auto-run interval in tests
      return 1;
    });
    window.showToast = jest.fn();
    axiosClient.get.mockReset();
    axiosClient.post.mockReset();
    axiosClient.patch.mockReset();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  it('posts choice using related_object_id as absorption_id', async () => {
    const notif = {
      id: 999,
      notification_type: 'teocoin_discount_pending',
      message:
        "Student X requested 20% discount on 'Course A'. Accept TEO: 10 TEO + 2.5 bonus = 12.5 TEO total. Keep EUR: €15. Decide within 24 hours.",
      related_object_id: 123, // the actual absorption id
      created_at: new Date().toISOString(),
      read: false
    };

    axiosClient.get.mockResolvedValueOnce({ data: [notif] });
    axiosClient.post.mockResolvedValueOnce({ data: { success: true, absorption: { id: 123, final_teacher_teo: 12.5 } } });
    axiosClient.patch.mockResolvedValueOnce({ data: { success: true } });

    render(<UnifiedTeacherNotifications />);

    // Open the dropdown
    const bell = await screen.findByRole('button');
    fireEvent.click(bell);

    // Click TEO button
    const teoBtn = await screen.findByRole('button', { name: /TEO/i });
    fireEvent.click(teoBtn);

    await waitFor(() => {
      expect(axiosClient.post).toHaveBeenCalled();
    });

    const [url, payload] = axiosClient.post.mock.calls[0];
    expect(url).toBe('/teocoin/teacher/choice/');
    expect(payload).toEqual({ absorption_id: 123, choice: 'teo' });
  });
});
