import React, { useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  BackgroundVariant,
  Panel,
  useReactFlow,
  SelectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useDiagramStore } from '../../../store/diagramStore';
import { nodeTypes, edgeTypes } from '../../../features/diagram-engine/NodeFactory';
import { EdgeMarkers } from '../../../components/edges/uml/UMLEdges';
import { DiagramToolbar } from '../DiagramToolbar/DiagramToolbar';
import { DiagramProperties } from '../DiagramProperties/DiagramProperties';
import { Save, AlertCircle } from 'lucide-react';

const DiagramCanvasContent: React.FC = () => {
  const reactFlowInstance = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // Store state and actions
  const {
    nodes,
    edges,
    diagramName,
    isDirty,
    isSaving,
    error,
    onNodesChange,
    onEdgesChange,
    addEdge,
    addNode,
    setViewport,
    saveDiagram,
    diagramType,
  } = useDiagramStore();

  // Handle connection between nodes
  const onConnect = useCallback(
    (connection: any) => {
      addEdge(connection);
    },
    [addEdge]
  );

  // Handle drop from palette
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type || !reactFlowWrapper.current) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      addNode(type, position);
    },
    [reactFlowInstance, addNode]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Save: Ctrl/Cmd + S
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        saveDiagram();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [saveDiagram]);

  // Sync viewport changes
  const onMove = useCallback(() => {
    const viewport = reactFlowInstance.getViewport();
    setViewport(viewport);
  }, [reactFlowInstance, setViewport]);

  return (
    <div className="h-full w-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-800">{diagramName}</h1>
          {isDirty && (
            <span className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}
          
          <button
            onClick={saveDiagram}
            disabled={!isDirty || isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save'}</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Toolbar */}
        <DiagramToolbar />

        {/* Canvas */}
        <div ref={reactFlowWrapper} className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onMove={onMove}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            attributionPosition="bottom-left"
            selectionMode={SelectionMode.Partial}
            multiSelectionKeyCode="Shift"
            deleteKeyCode="Delete"
            selectNodesOnDrag={false}
            snapToGrid
            snapGrid={[15, 15]}
            defaultEdgeOptions={{
              type: 'default',
              animated: false,
            }}
          >
            <Background 
              variant={BackgroundVariant.Dots} 
              gap={15} 
              size={1}
              color="#e5e7eb"
            />
            <Controls 
              showZoom
              showFitView
              showInteractive
              position="bottom-right"
            />
            <MiniMap 
              nodeColor={(node) => {
                if (node.type?.includes('ER')) return '#3b82f6';
                if (node.type?.includes('UML')) return '#8b5cf6';
                if (node.type?.includes('BPMN')) return '#10b981';
                return '#6b7280';
              }}
              maskColor="rgba(0, 0, 0, 0.1)"
              position="bottom-left"
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '4px',
              }}
            />
            
            {/* Custom panels */}
            <Panel position="top-center">
              <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-sm text-gray-600">
                {diagramType}
              </div>
            </Panel>

            {/* SVG markers for edges */}
            <EdgeMarkers />
          </ReactFlow>
        </div>

        {/* Properties panel */}
        <DiagramProperties />
      </div>
    </div>
  );
};

export const DiagramCanvas: React.FC = () => {
  return (
    <ReactFlowProvider>
      <DiagramCanvasContent />
    </ReactFlowProvider>
  );
};