// src/App.tsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import TopProgressBar from "./components/TopProgressBar";
import ToastHost from "./components/ToastHost";
import ErrorBoundary from "./components/ErrorBoundary";
import CourseDetail from "./pages/CourseDetail"
import CourseCheckout from "./pages/CourseCheckout"
import PaymentReturn from "./pages/PaymentReturn"
import { ProtectedRoute, RoleRoute } from "./routes/ProtectedRoute";
import CoursesList from "./pages/CoursesList";
import Notifications from "./pages/Notifications";
import Login from "./pages/Login";
import Register from "./pages/Register";
import VerifyEmail from "./pages/VerifyEmail";
import VerifyEmailSent from "./pages/VerifyEmailSent";
import Forbidden from "./pages/Forbidden";
import ProfilePage from "./pages/ProfilePage";
import StudentDashboard from "./pages/StudentDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import AdminDashboard from "./pages/AdminDashboard";

export default function App() {
  return (
    <>
      <TopProgressBar />
      <ToastHost />

      <Routes>
        <Route element={<AppLayout />}>
          {/* Public */}
          <Route index element={<Navigate to="/courses" replace />} />
          <Route path="/login" element={<ErrorBoundary><Login /></ErrorBoundary>} />
          <Route path="/register" element={<ErrorBoundary><Register /></ErrorBoundary>} />
          <Route path="/verify-email" element={<ErrorBoundary><VerifyEmail /></ErrorBoundary>} />
          <Route path="/verify-email/sent" element={<ErrorBoundary><VerifyEmailSent /></ErrorBoundary>} />
          <Route path="/forbidden" element={<ErrorBoundary><Forbidden /></ErrorBoundary>} />
          <Route path="/courses" element={<ErrorBoundary><CoursesList /></ErrorBoundary>} />
          <Route path="/courses/:id" element={<ErrorBoundary><CourseDetail /></ErrorBoundary>} />

          <Route
            path="courses/:id/checkout"
            element={
            <ProtectedRoute>
              <ErrorBoundary><CourseCheckout /></ErrorBoundary>
            </ProtectedRoute>            
            }          
            />

      <Route path="payments/return" element={<ErrorBoundary><PaymentReturn /></ErrorBoundary>} />
          {/* Protected (any role) */}
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <ErrorBoundary><Notifications /></ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ErrorBoundary><StudentDashboard /></ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ErrorBoundary><ProfilePage /></ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <RoleRoute allow="admin">
                <ErrorBoundary><AdminDashboard /></ErrorBoundary>
              </RoleRoute>
            }
          />


          {/* TEACHER only */}
          <Route
            path="/teacher"
            element={
              <RoleRoute allow="teacher">
                <ErrorBoundary><TeacherDashboard /></ErrorBoundary>
              </RoleRoute>
            }
          />

          {/* ADMIN only */}
          <Route
            path="/admin"
            element={
              <RoleRoute allow="admin">
                <ErrorBoundary><AdminDashboard /></ErrorBoundary>
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
