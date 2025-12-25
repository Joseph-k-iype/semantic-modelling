import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Pages
import LoginPage from './pages/LoginPage/LoginPage';
import HomePage from './pages/HomePage/HomePage';
import WorkspacePage from './pages/WorkspacePage/WorkspacePage';
import ModelEditorPage from './pages/ModelEditorPage/ModelEditorPage';

function App() {
  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/workspaces/:workspaceId" element={<WorkspacePage />} />
        <Route path="/models/:modelId" element={<ModelEditorPage />} />
        
        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      
      {/* Global toast notifications */}
      <Toaster position="top-right" />
    </>
  );
}

export default App;