// src/App.tsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import TopProgressBar from "./components/TopProgressBar";
import ToastHost from "./components/ToastHost";
import ErrorBoundary from "./components/ErrorBoundary";

import { ProtectedRoute, RoleRoute } from "./routes/ProtectedRoute";

import CoursesList from "./pages/CoursesList";
import CourseDetail from "./pages/CourseDetail";
import CourseCheckout from "./pages/CourseCheckout";
import Notifications from "./pages/Notifications";
import Login from "./pages/Login";
import Register from "./pages/Register";
import VerifyEmail from "./pages/VerifyEmail";
import VerifyEmailSent from "./pages/VerifyEmailSent";
import Forbidden from "./pages/Forbidden";
import ProfilePage from "./pages/ProfilePage";
import StudentDashboard from "./pages/StudentDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";

export default function App() {
  return (
    <>
      {/* UI globali */}
      <TopProgressBar />
      <ToastHost />

      {/* Layout route: AppLayout contiene <Outlet /> e la navbar */}
      <Routes>
        <Route element={<AppLayout />}>
          {/* Public */}
          <Route index element={<Navigate to="/courses" replace />} />
          <Route
            path="/login"
            element={
              <ErrorBoundary>
                <Login />
              </ErrorBoundary>
            }
          />
          <Route
            path="/register"
            element={
              <ErrorBoundary>
                <Register />
              </ErrorBoundary>
            }
          />
          <Route
            path="/verify-email"
            element={
              <ErrorBoundary>
                <VerifyEmail />
              </ErrorBoundary>
            }
          />
          <Route
            path="/verify-email/sent"
            element={
              <ErrorBoundary>
                <VerifyEmailSent />
              </ErrorBoundary>
            }
          />
          <Route
            path="/forbidden"
            element={
              <ErrorBoundary>
                <Forbidden />
              </ErrorBoundary>
            }
          />

          <Route
            path="/courses"
            element={
              <ErrorBoundary>
                <CoursesList />
              </ErrorBoundary>
            }
          />
          <Route
            path="/courses/:id"
            element={
              <ErrorBoundary>
                <CourseDetail />
              </ErrorBoundary>
            }
          />

          {/* Checkout corso (protetta) */}
          <Route
            path="/courses/:id/buy"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <CourseCheckout />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />

          {/* Protected */}
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <Notifications />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <StudentDashboard />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <ProfilePage />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />

          {/* Solo TEACHER */}
          <Route
            path="/teacher"
            element={
              <RoleRoute allow="teacher">
                <ErrorBoundary>
                  <TeacherDashboard />
                </ErrorBoundary>
              </RoleRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<Navigate to="/courses" replace />} />
        </Route>
      </Routes>
    </>
  );
}
