import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage/HomePage';
import { DiagramEditorPage } from './pages/DiagramEditorPage/DiagramEditorPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/diagram/new" element={<DiagramEditorPage />} />
        <Route path="/diagram/:id" element={<DiagramEditorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;