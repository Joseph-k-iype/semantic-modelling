// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage/HomePage';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { DiagramEditorPage } from './pages/DiagramEditorPage/DiagramEditorPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/diagram/new" element={<DiagramEditorPage />} />
        <Route path="/diagram/:id" element={<DiagramEditorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;