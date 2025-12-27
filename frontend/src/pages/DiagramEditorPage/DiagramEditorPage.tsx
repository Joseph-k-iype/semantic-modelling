import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DiagramCanvas } from '../../components/diagram/DiagramCanvas/DiagramCanvas';
import { useDiagramStore } from '../../store/diagramStore';
import { DiagramType } from '../../types/diagram.types';

export const DiagramEditorPage: React.FC = () => {
  const { diagramId } = useParams<{ diagramId: string }>();
  const navigate = useNavigate();
  const { loadDiagram, setDiagram, isLoading, error } = useDiagramStore();

  useEffect(() => {
    if (diagramId) {
      // Load existing diagram
      loadDiagram(diagramId);
    } else {
      // Create new diagram
      setDiagram({
        id: `diagram_${Date.now()}`,
        name: 'Untitled Diagram',
        type: DiagramType.UML_CLASS,
        modelId: 'model_1', // TODO: Get from route or context
        workspaceId: 'workspace_1', // TODO: Get from route or context
        nodes: [],
        edges: [],
      });
    }
  }, [diagramId]);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading diagram...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Error Loading Diagram</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <DiagramCanvas />
    </div>
  );
};