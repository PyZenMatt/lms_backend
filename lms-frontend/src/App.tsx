import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import { ProtectedRoute, RoleRoute } from "./routes/ProtectedRoute";
import ProtectedPing from "./components/ProtectedPing";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={
        <ProtectedRoute><Dashboard /></ProtectedRoute>
      }/>
      <Route path="/teacher" element={
        <RoleRoute allow={["teacher"]}><TeacherDashboard /></RoleRoute>
      }/>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
      <Route path="/me" element={
        <ProtectedRoute><ProtectedPing /></ProtectedRoute>
      }/>
    </Routes>
  );
}
