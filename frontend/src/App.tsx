// frontend/src/App.tsx
/**
 * Main Application Component
 * Semantic Architect - UML Ontology and Graph Modeling Platform
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AuthGuard from './components/auth/AuthGuard/AuthGuard';
import Layout from './components/layout/Layout';

// Pages - using named exports
import { HomePage } from './pages/HomePage/HomePage';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { WorkspacePage } from './pages/WorkspacePage/WorkspacePage';
import ModelEditorPage from './pages/ModelEditorPage/ModelEditorPage';
import { OntologyBuilderPage } from './pages/OntologyBuilderPage/OntologyBuilderPage';
import SettingsPage from './pages/SettingsPage/SettingsPage';
import { NotFoundPage } from './pages/NotFoundPage/NotFoundPage';
import ImportWorkflow from './pages/ImportWorkflow/ImportWorkflow';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Routes with Layout */}
        <Route
          path="/*"
          element={
            <AuthGuard>
              <Layout />
            </AuthGuard>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="workspace" element={<WorkspacePage />} />
          <Route path="workspace/:workspaceId" element={<WorkspacePage />} />
          <Route path="model/:modelId" element={<ModelEditorPage />} />
          <Route path="ontology" element={<OntologyBuilderPage />} />
          <Route path="ontology/:diagramId" element={<OntologyBuilderPage />} />
          
          {/* Import Feature Route */}
          <Route path="import" element={<ImportWorkflow />} />
          
          <Route path="settings" element={<SettingsPage />} />
          <Route path="404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;