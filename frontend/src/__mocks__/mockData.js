// Mock data realistici basati sui modelli Django del progetto
import { faker } from '@faker-js/faker';

// Seed per dati consistenti nei test
faker.seed(123);

export const mockData = {
  // ============== TOKENS ==============
  tokens: {
    access: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.mock.access.token',
    refresh: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.mock.refresh.token'
  },

  // ============== USERS ==============
  users: {
    student: {
      id: 1,
      username: 'student_test',
      email: 'student@test.com',
      first_name: 'Test',
      last_name: 'Student',
      user_type: 'student',
      profile: {
        bio: 'Test student bio',
        avatar: faker.image.avatar(),
        date_joined: '2024-01-01T00:00:00Z'
      },
      teocoin_balance: 250.00,
      is_active: true
    },
    teacher: {
      id: 2,
      username: 'teacher_test',
      email: 'teacher@test.com',
      first_name: 'Test',
      last_name: 'Teacher',
      user_type: 'teacher',
      profile: {
        bio: 'Experienced teacher in programming',
        avatar: faker.image.avatar(),
        specializations: ['Python', 'JavaScript', 'React']
      },
      teocoin_balance: 1000.00,
      is_active: true
    },
    admin: {
      id: 3,
      username: 'admin_test',
      email: 'admin@test.com',
      first_name: 'Test',
      last_name: 'Admin',
      user_type: 'admin',
      is_staff: true,
      is_superuser: true
    }
  },

  // ============== COURSES ==============
  courses: {
    list: [
      {
        id: 1,
        title: 'React Advanced Concepts',
        description: 'Learn advanced React patterns and best practices',
        price: 50.00,
        instructor: {
          id: 2,
          first_name: 'Test',
          last_name: 'Teacher'
        },
        difficulty: 'intermediate',
        duration_hours: 20,
        is_published: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
        enrolled_count: 45,
        rating: 4.5,
        category: 'programming'
      },
      {
        id: 2,
        title: 'Python for Beginners',
        description: 'Complete Python course from scratch',
        price: 30.00,
        instructor: {
          id: 2,
          first_name: 'Test',
          last_name: 'Teacher'
        },
        difficulty: 'beginner',
        duration_hours: 15,
        is_published: true,
        created_at: '2024-01-05T00:00:00Z',
        enrolled_count: 120,
        rating: 4.8,
        category: 'programming'
      }
    ]
  },

  // ============== DASHBOARDS ==============
  dashboards: {
    student: {
      enrolled_courses: [
        {
          id: 1,
          title: 'React Advanced Concepts',
          progress: 65,
          last_accessed: '2024-01-20T10:30:00Z',
          completion_status: 'in_progress'
        }
      ],
      recent_submissions: [
        {
          id: 1,
          exercise_title: 'React Hooks Exercise',
          score: 85,
          submitted_at: '2024-01-19T14:20:00Z'
        }
      ],
      teocoin_balance: 250.00,
      total_courses: 3,
      completed_courses: 1,
      achievements: [
        {
          id: 1,
          name: 'First Course Completed',
          icon: '🎓',
          earned_at: '2024-01-10T00:00:00Z'
        }
      ]
    },
    teacher: {
      created_courses: [
        {
          id: 1,
          title: 'React Advanced Concepts',
          enrolled_students: 45,
          revenue: 2250.00,
          status: 'published'
        },
        {
          id: 2,
          title: 'Python for Beginners',
          enrolled_students: 120,
          revenue: 3600.00,
          status: 'published'
        }
      ],
      total_revenue: 5850.00,
      total_students: 165,
      average_rating: 4.6,
      pending_reviews: 3
    }
  },

  // ============== EXERCISES ==============
  exercises: {
    submissions: [
      {
        id: 1,
        exercise: {
          id: 1,
          title: 'React State Management',
          description: 'Implement state management with useState'
        },
        code: 'const [count, setCount] = useState(0);',
        score: 85,
        feedback: 'Good implementation! Consider using useReducer for complex state.',
        submitted_at: '2024-01-19T14:20:00Z',
        status: 'graded'
      },
      {
        id: 2,
        exercise: {
          id: 2,
          title: 'Component Composition',
          description: 'Create reusable components'
        },
        code: 'const Button = ({ children, onClick }) => <button onClick={onClick}>{children}</button>;',
        score: 92,
        feedback: 'Excellent component design!',
        submitted_at: '2024-01-18T09:15:00Z',
        status: 'graded'
      }
    ]
  },

  // ============== BLOCKCHAIN ==============
  blockchain: {
    balance: 250.00,
    address: '0x742d35Cc6634C0532925a3b8D404e3C582854556',
    transactionHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    network: 'sepolia'
  },

  // ============== NOTIFICATIONS ==============
  notifications: {
    list: [
      {
        id: 1,
        title: 'Course Update',
        message: 'New lesson added to React Advanced Concepts',
        type: 'course_update',
        is_read: false,
        created_at: '2024-01-20T12:00:00Z'
      },
      {
        id: 2,
        title: 'Assignment Graded',
        message: 'Your React Hooks assignment has been graded',
        type: 'grade',
        is_read: true,
        created_at: '2024-01-19T15:30:00Z'
      }
    ],
    unreadCount: 1
  },

  // ============== CHAT ==============
  chat: {
    messages: [
      {
        id: 1,
        content: 'Hello, I need help with React hooks',
        sender: {
          id: 1,
          first_name: 'Test',
          last_name: 'Student'
        },
        timestamp: '2024-01-20T10:00:00Z',
        type: 'text'
      },
      {
        id: 2,
        content: 'Sure! What specific issue are you facing?',
        sender: {
          id: 2,
          first_name: 'Test',
          last_name: 'Teacher'
        },
        timestamp: '2024-01-20T10:05:00Z',
        type: 'text'
      }
    ]
  },

  // ============== ERRORS ==============
  errors: {
    validation: {
      non_field_errors: ['Invalid credentials'],
      email: ['This field is required'],
      password: ['Password too short']
    },
    network: {
      detail: 'Network error - please try again',
      code: 'NETWORK_ERROR'
    },
    server: {
      detail: 'Internal server error',
      code: 'SERVER_ERROR'
    }
  }
};
