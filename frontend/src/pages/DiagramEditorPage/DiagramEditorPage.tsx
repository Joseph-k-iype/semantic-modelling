// frontend/src/pages/DiagramEditorPage/DiagramEditorPage.tsx
import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { DiagramCanvas } from '../../components/diagram/DiagramCanvas/DiagramCanvas';
import { useDiagramStore } from '../../store/diagramStore';
import { DiagramType } from '../../types/diagram.types';
import { ArrowLeft, Save, Download, Share2, History } from 'lucide-react';

export const DiagramEditorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { 
    loadDiagram, 
    setDiagram, 
    setDiagramType,
    isLoading, 
    error,
    nodes,
    edges,
    diagramName,
    saveDiagram,
    isSaving
  } = useDiagramStore();

  useEffect(() => {
    // Get diagram type and name from URL params
    const type = searchParams.get('type') || 'UML_CLASS';
    const name = searchParams.get('name') || 'Untitled Diagram';
    const id = searchParams.get('id');
    
    // Map string to DiagramType enum
    let diagramTypeEnum: DiagramType = DiagramType.UML_CLASS;
    
    switch (type) {
      case 'ER':
        diagramTypeEnum = DiagramType.ER;
        break;
      case 'UML_CLASS':
        diagramTypeEnum = DiagramType.UML_CLASS;
        break;
      case 'UML_SEQUENCE':
        diagramTypeEnum = DiagramType.UML_SEQUENCE;
        break;
      case 'UML_ACTIVITY':
        diagramTypeEnum = DiagramType.UML_ACTIVITY;
        break;
      case 'UML_STATE':
        diagramTypeEnum = DiagramType.UML_STATE;
        break;
      case 'BPMN':
        diagramTypeEnum = DiagramType.BPMN;
        break;
      default:
        diagramTypeEnum = DiagramType.UML_CLASS;
    }

    if (id) {
      // Load existing diagram
      loadDiagram(id);
    } else {
      // Create new diagram
      setDiagram({
        diagramId: `diagram_${Date.now()}`,
        diagramName: name,
        diagramType: diagramTypeEnum,
        nodes: [],
        edges: [],
      });
      setDiagramType(diagramTypeEnum);
    }
  }, [searchParams, loadDiagram, setDiagram, setDiagramType]);

  const handleSave = async () => {
    await saveDiagram();
  };

  const handleExport = () => {
    // TODO: Implement export
    console.log('Export diagram');
  };

  const handleShare = () => {
    // TODO: Implement share
    console.log('Share diagram');
  };

  const handleViewHistory = () => {
    // TODO: Implement version history
    console.log('View history');
  };

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
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Navbar */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            
            <div className="h-6 w-px bg-gray-300" />
            
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{diagramName}</h1>
              <p className="text-xs text-gray-500">
                {nodes.length} nodes • {edges.length} connections
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleViewHistory}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <History className="w-4 h-4" />
              History
            </button>

            <button
              onClick={handleShare}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Share2 className="w-4 h-4" />
              Share
            </button>

            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </button>

            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>

      {/* Diagram Canvas */}
      <div className="flex-1 overflow-hidden">
        <DiagramCanvas />
      </div>
    </div>
  );
};