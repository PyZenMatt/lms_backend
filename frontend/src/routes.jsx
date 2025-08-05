import React, { Suspense, Fragment, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Loader from './components/Loader/Loader';
import AdminLayout from './layouts/AdminLayout';

import { BASE_URL } from './config/constant';

export const renderRoutes = (routes = []) => (
  <Suspense fallback={<Loader />}>
    <Routes>
      {routes.map((route, i) => {
        const Guard = route.guard || Fragment;
        const Layout = route.layout || Fragment;
        const Element = route.element;

        return (
          <Route
            key={i}
            path={route.path}
            element={
              <Guard>
                <Layout>{route.routes ? renderRoutes(route.routes) : <Element props={true} />}</Layout>
              </Guard>
            }
          />
        );
      })}
    </Routes>
  </Suspense>
);

const routes = [
  {
    exact: 'true',
    path: '/',
    element: lazy(() => import('./views/landing/TeoArtLandingNew'))
  },
  {
    exact: 'true',
    path: '/landing',
    element: lazy(() => import('./views/landing/TeoArtLandingNew'))
  },
  {
    exact: 'true',
    path: '/login',
    element: lazy(() => import('./views/auth/signin/SignIn1'))
  },
  {
    exact: 'true',
    path: '/auth/signin-1',
    element: lazy(() => import('./views/auth/signin/SignIn1'))
  },
  {
    exact: 'true',
    path: '/auth/signup-1',
    element: lazy(() => import('./views/auth/signup/SignUpNew'))
  },
  {
    path: '*',
    layout: AdminLayout,
    routes: [

      {
        exact: 'true',
        path: '/corsi',
        element: lazy(() => import('./views/courses/AllCourses'))
      },
      {
        exact: 'true',
        path: '/dashboard/student',
        element: lazy(() => import('./views/dashboard/StudentDashboard'))
      },
      {
        exact: 'true',
        path: '/dashboard/teacher',
        element: lazy(() => import('./views/dashboard/TeacherDashboard'))
      },
      {
        path: '*',
        exact: 'true',
        element: () => <Navigate to={BASE_URL} />
      },
      {
        path: '/corsi/:courseId',
        element: lazy(() => import('./views/courses/StudentCourseDetailNew'))
      },
      {
        path: '/lezioni/:lessonId',
        element: lazy(() => import('./views/courses/StudentLessonDetailNew'))
      },
      {
        path: '/esercizi/:exerciseId',
        element: lazy(() => import('./views/courses/StudentExerciseDetailNew'))
      },
      {
        path: '/submission-graded/:submissionId',
        element: lazy(() => import('./views/courses/ExerciseGradedDetail'))
      },
      {
        exact: 'true',
        path: '/review/assigned',
        element: lazy(() => import('./views/review/AssignedReviewsList'))
      },
      {
        exact: 'true',
        path: '/review/:submissionId',
        element: lazy(() => import('./views/review/ReviewDetail'))
      },
      {
        path: '/corsi-docente/:courseId',
        element: lazy(() => import('./views/courses/TeacherCourseDetail'))
      },
      {
        path: '/lezioni-docente/:lessonId',
        element: lazy(() => import('./views/courses/TeacherLessonDetail'))
      },
      {
        path: '/esercizi-docente/:exerciseId',
        element: lazy(() => import('./views/courses/TeacherExerciseDetail'))
      },
      {
        exact: 'true',
        path: '/profile',
        element: lazy(() => import('./views/profile/UserProfileNew'))
      },
      {
        exact: 'true',
        path: '/profile/notifications',
        element: lazy(() => import('./views/profile/NotificationListNew'))
      },
      {
        exact: 'true',
        path: '/profile/settings',
        element: lazy(() => import('./views/profile/ProfileSettings'))
      },
      {
        exact: 'true',
        path: '/profile/settings/theme',
        element: lazy(() => import('./views/settings/ThemeSettings'))
      },
      {
        exact: 'true',
        path: '/demo/dark-theme',
        element: lazy(() => import('./views/demo/DarkThemeShowcase'))
      },
      {
        exact: 'true',
        path: '/dev/status',
        element: lazy(() => import('./views/dev/DevelopmentStatusDashboard'))
      },
      {
        exact: 'true',
        path: '/profile/progress',
        element: lazy(() => import('./views/profile/ProfileProgress'))
      },
      {
        exact: 'true',
        path: '/dashboard/admin',
        element: lazy(() => import('./views/admin/AdminDashboard'))
      },
      {
        exact: 'true',
        path: '/admin/reward-pool',
        element: lazy(() => import('./views/admin/RewardPoolDashboard'))
      },
      {
        exact: 'true',
        path: '/admin/pending-courses',
        element: lazy(() => import('./views/admin/PendingCoursesTable'))
      },
      {
        path: '/admin/corsi/:courseId',
        element: lazy(() => import('./views/admin/AdminCourseDetail'))
      },
      {
        path: '/admin/lezioni/:lessonId',
        element: lazy(() => import('./views/admin/AdminLessonDetail'))
      },
      {
        path: '/admin/esercizi/:exerciseId',
        element: lazy(() => import('./views/admin/AdminExerciseDetail'))
      },

    ]
  }
];

export default routes;
