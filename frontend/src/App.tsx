import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage/HomePage';
import LoginPage from './pages/LoginPage/LoginPage';
import WorkspacePage from './pages/WorkspacePage/WorkspacePage';
import ModelEditorPage from './pages/ModelEditorPage/ModelEditorPage';
import DiagramEditorPage from './pages/DiagramEditorPage/DiagramEditorPage';
import SettingsPage from './pages/SettingsPage/SettingsPage';
import NotFoundPage from './pages/NotFoundPage/NotFoundPage';
import AuthGuard from './components/auth/AuthGuard/AuthGuard';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes */}
        <Route path="/" element={<AuthGuard><HomePage /></AuthGuard>} />
        <Route path="/workspace/:workspaceId" element={<AuthGuard><WorkspacePage /></AuthGuard>} />
        <Route path="/model/:modelId" element={<AuthGuard><ModelEditorPage /></AuthGuard>} />
        <Route path="/diagram/:diagramId" element={<AuthGuard><DiagramEditorPage /></AuthGuard>} />
        <Route path="/settings" element={<AuthGuard><SettingsPage /></AuthGuard>} />
        
        {/* Fallback Routes */}
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </Router>
  );
};

export default App;