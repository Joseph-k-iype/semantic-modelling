/**
 * Ontology Builder Page - Main Editor
 * Path: frontend/src/pages/OntologyBuilderPage/OntologyBuilderPage.tsx
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  ReactFlowInstance,
  ConnectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  MousePointer, 
  Hand, 
  Undo2, 
  Redo2, 
  ZoomIn, 
  ZoomOut,
  Save,
  Upload,
} from 'lucide-react';
import { apiClient } from '../../services/api/client';
import { COLORS, ELEMENT_COLORS } from '../../constants/colors';
import type { NodeData, EdgeData, NodeType } from '../../types/diagram.types';

// Import components that we'll create next
import { ElementPalette } from '../../components/builder/ElementPalette/ElementPalette';
import { HierarchyView } from '../../components/builder/HierarchyView/HierarchyView';
import { CardinalityModal } from '../../components/modals/CardinalityModal/CardinalityModal';
import { ClassNode } from '../../components/nodes/ClassNode/ClassNode';

// Node types registry
const nodeTypes = {
  package: ClassNode,
  class: ClassNode,
  object: ClassNode,
  interface: ClassNode,
  enumeration: ClassNode,
};

interface PendingConnection {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export const OntologyBuilderPage: React.FC = () => {
  const { id: diagramId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  // UI state
  const [activeTab, setActiveTab] = useState<'elements' | 'hierarchy'>('elements');
  const [selectedTool, setSelectedTool] = useState<'select' | 'pan'>('select');
  const [diagramName, setDiagramName] = useState('Untitled Diagram');
  const [workspaceName, setWorkspaceName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // Cardinality modal state
  const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null);
  const [showCardinalityModal, setShowCardinalityModal] = useState(false);
  
  // History for undo/redo
  const [history, setHistory] = useState<{ nodes: Node[]; edges: Edge[] }[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // Counter for unique IDs
  const nodeIdCounter = useRef(1);

  // Load diagram on mount
  useEffect(() => {
    if (diagramId && diagramId !== 'new') {
      loadDiagram(diagramId);
    } else {
      setIsLoading(false);
    }
  }, [diagramId]);

  // Save to history whenever nodes or edges change
  useEffect(() => {
    if (!isLoading && nodes.length > 0) {
      saveToHistory();
    }
  }, [nodes, edges]);

  const loadDiagram = async (id: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.get(`/diagrams/${id}`);
      const diagram = response.data;
      
      setDiagramName(diagram.name);
      setWorkspaceName(diagram.workspace_name || '');
      
      if (diagram.nodes && diagram.nodes.length > 0) {
        setNodes(diagram.nodes);
      }
      if (diagram.edges && diagram.edges.length > 0) {
        setEdges(diagram.edges);
      }
      if (diagram.viewport && reactFlowInstance) {
        reactFlowInstance.setViewport(diagram.viewport);
      }
    } catch (error) {
      console.error('Failed to load diagram:', error);
      alert('Failed to load diagram. Redirecting to home.');
      navigate('/');
    } finally {
      setIsLoading(false);
    }
  };

  const saveToHistory = () => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({ nodes: [...nodes], edges: [...edges] });
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      setNodes(prevState.nodes);
      setEdges(prevState.edges);
      setHistoryIndex(historyIndex - 1);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setNodes(nextState.nodes);
      setEdges(nextState.edges);
      setHistoryIndex(historyIndex + 1);
    }
  };

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow') as NodeType;
      
      if (!type || !reactFlowInstance) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node<NodeData> = {
        id: `node_${nodeIdCounter.current++}`,
        type: type,
        position,
        data: {
          label: type.charAt(0).toUpperCase() + type.slice(1),
          type: type as any,
          stereotype: '',
          color: ELEMENT_COLORS[type],
          attributes: type === 'package' ? [] : [
            {
              id: 'attr_1',
              name: 'field 1',
              dataType: 'INTEGER',
              key: 'PRIMARY KEY',
            },
            {
              id: 'attr_2',
              name: 'field 2',
              dataType: 'VARCHAR',
              key: 'Default',
            },
          ],
          methods: type === 'interface' ? [
            {
              id: 'method_1',
              name: 'method1',
              returnType: 'void',
              parameters: [],
            },
          ] : [],
          literals: type === 'enumeration' ? ['OPTION_1', 'OPTION_2'] : [],
        } as any,
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) {
        return;
      }

      // Store pending connection and show cardinality modal
      setPendingConnection({
        source: connection.source,
        target: connection.target,
        sourceHandle: connection.sourceHandle || undefined,
        targetHandle: connection.targetHandle || undefined,
      });
      setShowCardinalityModal(true);
    },
    []
  );

  const handleCardinalitySubmit = useCallback(
    (config: {
      sourceCardinality: string;
      targetCardinality: string;
      type: string;
      label?: string;
    }) => {
      if (!pendingConnection) return;

      const newEdge: Edge<EdgeData> = {
        id: `edge_${Date.now()}`,
        source: pendingConnection.source,
        target: pendingConnection.target,
        sourceHandle: pendingConnection.sourceHandle,
        targetHandle: pendingConnection.targetHandle,
        type: 'default',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: COLORS.BLACK,
        },
        label: config.label || config.type,
        data: {
          type: config.type as any,
          sourceCardinality: config.sourceCardinality,
          targetCardinality: config.targetCardinality,
          label: config.label,
          color: COLORS.BLACK,
        },
      };

      setEdges((eds) => addEdge(newEdge, eds));
      setShowCardinalityModal(false);
      setPendingConnection(null);
    },
    [pendingConnection, setEdges]
  );

  const handleSave = async () => {
    try {
      setIsSaving(true);

      const viewport = reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 };

      const payload = {
        nodes,
        edges,
        viewport,
      };

      if (diagramId && diagramId !== 'new') {
        await apiClient.put(`/diagrams/${diagramId}`, payload);
      } else {
        const response = await apiClient.post('/diagrams', {
          ...payload,
          name: diagramName,
          workspace_name: workspaceName,
        });
        navigate(`/builder/${response.data.id}`, { replace: true });
      }

      alert('Diagram saved successfully!');
    } catch (error) {
      console.error('Failed to save diagram:', error);
      alert('Failed to save diagram. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!diagramId || diagramId === 'new') {
      alert('Please save the diagram before publishing.');
      return;
    }

    try {
      setIsPublishing(true);
      await apiClient.post(`/diagrams/${diagramId}/publish`);
      alert('Diagram published successfully!');
    } catch (error) {
      console.error('Failed to publish diagram:', error);
      alert('Failed to publish diagram. Please try again.');
    } finally {
      setIsPublishing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div
          className="animate-spin rounded-full h-16 w-16 border-4 border-solid"
          style={{
            borderColor: COLORS.LIGHT_GREY,
            borderTopColor: COLORS.PRIMARY,
          }}
        />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: COLORS.OFF_WHITE }}>
      {/* Top Header */}
      <header
        className="flex items-center justify-between px-6 py-3 border-b shadow-sm"
        style={{ backgroundColor: COLORS.WHITE, borderColor: COLORS.LIGHT_GREY }}
      >
        <h1 className="text-2xl font-bold" style={{ color: COLORS.BLACK }}>
          SEMANTIC ARCHITECT
        </h1>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 rounded text-white transition hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: COLORS.PRIMARY }}
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Diagram'}
          </button>

          <button
            onClick={handlePublish}
            disabled={isPublishing || !diagramId || diagramId === 'new'}
            className="flex items-center gap-2 px-4 py-2 rounded text-white transition hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: COLORS.ERROR }}
          >
            <Upload className="w-4 h-4" />
            {isPublishing ? 'Publishing...' : 'Publish Diagram'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className="w-64 border-r overflow-y-auto"
          style={{ backgroundColor: COLORS.WHITE, borderColor: COLORS.LIGHT_GREY }}
        >
          {/* Tabs */}
          <div className="flex border-b" style={{ borderColor: COLORS.LIGHT_GREY }}>
            <button
              onClick={() => setActiveTab('elements')}
              className="flex-1 py-2 text-sm font-medium transition"
              style={{
                backgroundColor: activeTab === 'elements' ? COLORS.WARNING : COLORS.OFF_WHITE,
                color: activeTab === 'elements' ? COLORS.WHITE : COLORS.BLACK,
              }}
            >
              Elements
            </button>
            <button
              onClick={() => setActiveTab('hierarchy')}
              className="flex-1 py-2 text-sm font-medium transition"
              style={{
                backgroundColor: activeTab === 'hierarchy' ? COLORS.PRIMARY : COLORS.OFF_WHITE,
                color: activeTab === 'hierarchy' ? COLORS.WHITE : COLORS.BLACK,
              }}
            >
              Hierarchy
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-4">
            {activeTab === 'elements' ? (
              <ElementPalette />
            ) : (
              <HierarchyView nodes={nodes} />
            )}
          </div>
        </aside>

        {/* Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            nodeTypes={nodeTypes}
            connectionMode={ConnectionMode.Loose}
            fitView
            panOnScroll={selectedTool === 'pan'}
            selectionOnDrag={selectedTool === 'select'}
          >
            <Background color={COLORS.LIGHT_GREY} />
            <Controls showInteractive={false} />
          </ReactFlow>

          {/* Bottom Toolbar */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
            <div
              className="flex gap-2 rounded-lg shadow-lg p-2 border"
              style={{ backgroundColor: COLORS.WHITE, borderColor: COLORS.LIGHT_GREY }}
            >
              <button
                onClick={() => setSelectedTool('select')}
                className={`p-3 rounded transition ${
                  selectedTool === 'select' ? 'bg-gray-200' : 'hover:bg-gray-100'
                }`}
                title="Pointer"
              >
                <MousePointer className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
              <button
                onClick={() => setSelectedTool('pan')}
                className={`p-3 rounded transition ${
                  selectedTool === 'pan' ? 'bg-gray-200' : 'hover:bg-gray-100'
                }`}
                title="Pan"
              >
                <Hand className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
              <div className="w-px bg-gray-300 mx-1" />
              <button
                onClick={handleUndo}
                disabled={historyIndex <= 0}
                className="p-3 rounded transition hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Undo"
              >
                <Undo2 className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
              <button
                onClick={handleRedo}
                disabled={historyIndex >= history.length - 1}
                className="p-3 rounded transition hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Redo"
              >
                <Redo2 className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
              <div className="w-px bg-gray-300 mx-1" />
              <button
                onClick={() => reactFlowInstance?.zoomIn()}
                className="p-3 rounded transition hover:bg-gray-100"
                title="Zoom In"
              >
                <ZoomIn className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
              <button
                onClick={() => reactFlowInstance?.zoomOut()}
                className="p-3 rounded transition hover:bg-gray-100"
                title="Zoom Out"
              >
                <ZoomOut className="w-5 h-5" style={{ color: COLORS.BLACK }} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Cardinality Modal */}
      {showCardinalityModal && (
        <CardinalityModal
          isOpen={showCardinalityModal}
          onClose={() => {
            setShowCardinalityModal(false);
            setPendingConnection(null);
          }}
          onSubmit={handleCardinalitySubmit}
          sourceNode={nodes.find((n) => n.id === pendingConnection?.source)}
          targetNode={nodes.find((n) => n.id === pendingConnection?.target)}
        />
      )}
    </div>
  );
};

export default OntologyBuilderPage;