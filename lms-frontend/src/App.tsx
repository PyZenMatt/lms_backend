// src/App.tsx
// React import not required with new JSX transform
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import TopProgressBar from "./components/TopProgressBar";
import ToastHost from "./components/ToastHost";
import ErrorBoundary from "./components/ErrorBoundary";
import CourseDetail from "./pages/CourseDetail"
import CourseCheckout from "./pages/CourseCheckout"
import PaymentReturn from "./pages/PaymentReturn"
import StudentCourse from "./pages/StudentCourse"
import MyExercises from "./pages/MyExercises"
import ExerciseSubmit from "./pages/ExerciseSubmit"
import LessonPage from "./pages/LessonPage"
import ReviewsAssigned from "./pages/ReviewsAssigned"
import ReviewSubmission from "./pages/ReviewSubmission"
import ReviewsHistory from "./pages/ReviewsHistory"
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
import CoursesStudioList from "./pages/studio/CoursesStudioList"
import CourseStudioForm from "./pages/studio/CourseStudioForm"
import CourseBuilder from "./pages/studio/CourseBuilder"
import { useParams } from "react-router-dom";
import WalletPage from "./pages/WalletPage";

function BuyRedirect() {
  const { id } = useParams();
  return <Navigate to={`/courses/${id}/checkout`} replace />;
}

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
              path="/learn/:id"
              element={
                <ProtectedRoute>
                  <ErrorBoundary><StudentCourse /></ErrorBoundary>
                </ProtectedRoute>
              }
            />

            <Route
              path="/my/exercises"
              element={
                <ProtectedRoute>
                  <ErrorBoundary><MyExercises /></ErrorBoundary>
                </ProtectedRoute>
              }
            />

            <Route
              path="/exercises/:id/submit"
              element={
                <ProtectedRoute>
                  <ErrorBoundary><ExerciseSubmit /></ErrorBoundary>
                </ProtectedRoute>
              }
            />

            <Route
              path="/lessons/:id"
              element={
                <ProtectedRoute>
                  <ErrorBoundary><LessonPage /></ErrorBoundary>
                </ProtectedRoute>
              }
            />

            <Route
              path="/courses/:id/checkout"
              element={
                <ProtectedRoute>
                  <ErrorBoundary><CourseCheckout /></ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses/:id/buy"
              element={<BuyRedirect />}
            />
            <Route path="/payments/return" element={<ErrorBoundary><PaymentReturn /></ErrorBoundary>} />
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
            path="/reviews/assigned"
            element={
              <ProtectedRoute>
                <ErrorBoundary><ReviewsAssigned /></ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reviews/:id/review"
            element={
              <ProtectedRoute>
                <ErrorBoundary><ReviewSubmission /></ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reviews/history"
            element={
              <ProtectedRoute>
                <ErrorBoundary><ReviewsHistory /></ErrorBoundary>
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

          {/* Studio (teacher) */}
          <Route path="studio/courses" element={<ProtectedRoute><ErrorBoundary><CoursesStudioList /></ErrorBoundary></ProtectedRoute>} />
          <Route path="studio/courses/new" element={<ProtectedRoute><ErrorBoundary><CourseStudioForm /></ErrorBoundary></ProtectedRoute>} />
          <Route path="studio/courses/:id/edit" element={<ProtectedRoute><ErrorBoundary><CourseStudioForm /></ErrorBoundary></ProtectedRoute>} />
          <Route path="studio/courses/:id/builder" element={<ProtectedRoute><ErrorBoundary><CourseBuilder /></ErrorBoundary></ProtectedRoute>} />

          {/* ADMIN only */}
          <Route
            path="/admin"
            element={
              <RoleRoute allow="admin">
                <ErrorBoundary><AdminDashboard /></ErrorBoundary>
              </RoleRoute>
            }
          />

          {/* Wallet */}
          <Route
            path="/wallet"
            element={
              <ProtectedRoute>
                <ErrorBoundary><WalletPage /></ErrorBoundary>
              </ProtectedRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<Navigate to="/courses" replace />} />
        </Route>
      </Routes>
    </>
  );
}
