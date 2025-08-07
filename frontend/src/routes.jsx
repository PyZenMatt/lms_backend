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

// Route configuration array
const routes = [
  {
    exact: 'true',
    path: '/',
    element: lazy(() => import('./views/landing/TeoArtLandingNew.jsx'))
  },
  {
    exact: 'true',
    path: '/landing',
    element: lazy(() => import('./views/landing/TeoArtLandingNew.jsx'))
  },
  {
    exact: 'true',
    path: '/login',
    element: lazy(() => import('./views/auth/signin/SignIn1.jsx'))
  },
  {
    exact: 'true',
    path: '/auth/signin-1',
    element: lazy(() => import('./views/auth/signin/SignIn1.jsx'))
  },
  {
    exact: 'true',
    path: '/auth/signup-1',
    element: lazy(() => import('./views/auth/signup/SignUpNew.jsx'))
  },
  {
    path: '*',
    layout: AdminLayout,
    routes: [
      {
        exact: 'true',
        path: '/corsi',
        element: lazy(() => import('./views/courses/AllCourses.jsx'))
      },
      {
        exact: 'true',
        path: '/dashboard',
        element: lazy(() => import('./components/common/DashboardRedirect.jsx'))
      },
      {
        exact: 'true',
        path: '/dashboard/student',
        element: lazy(() => import('./views/dashboard/StudentDashboard.jsx'))
      },
      {
        exact: 'true',
        path: '/dashboard/teacher',
        element: lazy(() => import('./views/dashboard/TeacherDashboard.jsx'))
      },
      {
        exact: 'true',
        path: '/dashboard/admin',
        element: lazy(() => import('./views/admin/AdminDashboard.jsx'))
      },
      {
        path: '/corsi/:courseId',
        element: lazy(() => import('./views/courses/StudentCourseDetailNew.jsx'))
      },
      {
        path: '/lezioni/:lessonId',
        element: lazy(() => import('./views/courses/StudentLessonDetailNew.jsx'))
      },
      {
        path: '/esercizi/:exerciseId',
        element: lazy(() => import('./views/courses/StudentExerciseDetailNew.jsx'))
      },
      {
        path: '/esercizi/:exerciseId/voto',
        element: lazy(() => import('./views/courses/ExerciseGradedDetail.jsx'))
      },
      {
        path: '/review/assigned',
        element: lazy(() => import('./views/review/AssignedReviewsList.jsx'))
      },
      {
        path: '/review/:reviewId',
        element: lazy(() => import('./views/review/ReviewDetail.jsx'))
      },
      {
        path: '/corsi-docente/:courseId',
        element: lazy(() => import('./views/courses/TeacherCourseDetail.jsx'))
      },
      {
        path: '/lezioni-docente/:lessonId',
        element: lazy(() => import('./views/courses/TeacherLessonDetail.jsx'))
      },
      {
        path: '/esercizi-docente/:exerciseId',
        element: lazy(() => import('./views/courses/TeacherExerciseDetail.jsx'))
      },
      // Teacher action routes
      {
        path: '/teacher/absorptions',
        element: lazy(() => import('./components/teacher/TeacherAbsorptionDashboard.jsx'))
      },
      {
        path: '/teacher/corsi/:courseId/edit',
        element: lazy(() => import('./views/courses/TeacherCourseDetail.jsx'))
      },
      {
        path: '/teacher/corsi/:courseId/preview',
        element: lazy(() => import('./views/courses/TeacherCourseDetail.jsx'))
      },
      {
        path: '/teacher/corsi/:courseId/lezioni/nuova',
        element: lazy(() => import('./views/courses/TeacherLessonDetail.jsx'))
      },
      {
        path: '/teacher/lezioni/:lessonId/edit',
        element: lazy(() => import('./views/courses/TeacherLessonDetail.jsx'))
      },
      {
        path: '/teacher/lezioni/:lessonId/preview',
        element: lazy(() => import('./views/courses/TeacherLessonDetail.jsx'))
      },
      {
        path: '/teacher/lezioni/:lessonId/esercizi/nuovo',
        element: lazy(() => import('./views/courses/TeacherExerciseDetail.jsx'))
      },
      {
        path: '/teacher/esercizi/:exerciseId/edit',
        element: lazy(() => import('./views/courses/TeacherExerciseDetail.jsx'))
      },
      {
        path: '/teacher/esercizi/:exerciseId/preview',
        element: lazy(() => import('./views/courses/TeacherExerciseDetail.jsx'))
      },
      // Admin routes
      {
        path: '/admin',
        element: lazy(() => import('./views/admin/AdminDashboard.jsx'))
      },
      {
        path: '/admin/corsi/:courseId',
        element: lazy(() => import('./views/admin/AdminCourseDetail.jsx'))
      },
      // Default redirect
      {
        path: '*',
        element: () => <Navigate to="/dashboard" replace />
      }
    ]
  }
];

export default routes;
