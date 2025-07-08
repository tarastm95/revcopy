import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, ProtectedRoute } from "./context/AuthContext";

// Pages
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Dashboard from "./pages/Dashboard";
import UsersPage from "./pages/UsersPage";
import PaymentsPage from "./pages/PaymentsPage";
import PromptsPage from "./pages/PromptsPage";
import AdminsPage from "./pages/AdminsPage";
import CrawlerPage from "./pages/CrawlerPage";
import AmazonPage from "./pages/AmazonPage";
import PerformanceOverview from "./pages/PerformanceOverview";
import MonitoringHealth from "./pages/MonitoringHealth";
import SystemMaintenance from "./pages/SystemMaintenance";
import {
  PerformanceRealtime,
  PerformanceDatabase,
  PerformanceCache,
  PerformanceTasks,
  MonitoringAlerts,
  MonitoringSecurity,
  MonitoringLogs,
} from "./pages/PlaceholderPages";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/users" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <UsersPage />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/payments" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PaymentsPage />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/prompts" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PromptsPage />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/admins" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <AdminsPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Performance Routes */}
            <Route 
              path="/performance/overview" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PerformanceOverview />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/performance/realtime" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PerformanceRealtime />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/performance/database" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PerformanceDatabase />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/performance/cache" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PerformanceCache />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/performance/tasks" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <PerformanceTasks />
                </ProtectedRoute>
              } 
            />
            
            {/* Monitoring Routes */}
            <Route 
              path="/monitoring/health" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <MonitoringHealth />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/monitoring/alerts" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <MonitoringAlerts />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/monitoring/security" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <MonitoringSecurity />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/monitoring/logs" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <MonitoringLogs />
                </ProtectedRoute>
              } 
            />
            
            {/* System Routes */}
            <Route 
              path="/system/maintenance" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <SystemMaintenance />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/system/crawler" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <CrawlerPage />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/system/amazon" 
              element={
                <ProtectedRoute fallback={<Navigate to="/login" replace />}>
                  <AmazonPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Catch-all 404 Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
