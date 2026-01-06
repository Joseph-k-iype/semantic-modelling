// frontend/src/pages/OntologyBuilderPage/OntologyBuilderPage.tsx
/**
 * Ontology Builder Page - FIXED: 409 Issue & UI Update
 * Path: frontend/src/pages/OntologyBuilderPage/OntologyBuilderPage.tsx
 * 
 * FIXES:
 * - No 409 conflict (tracks current diagram ID separately)
 * - UI updates diagram name after save
 * - Proper graph structure (attributes as properties)
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
import { COLORS, ELEMENT_COLORS } from '../../constants/colors';
import type { NodeData, EdgeData, NodeType } from '../../types/diagram.types';

// API Client
import { apiClient } from '../../services/api/client';

// Import components
import { ElementPalette } from '../../components/builder/ElementPalette/ElementPalette';
import { HierarchyView } from '../../components/builder/HierarchyView/HierarchyView';
import { CardinalityModal } from '../../components/modals/CardinalityModal/CardinalityModal';
import { DiagramNameModal } from '../../components/modals/DiagramNameModal/DiagramNameModal';
import { ElementEditor } from '../../components/builder/ElementEditor/ElementEditor';
import { FalkorDebugPanel } from '../../components/debug/FalkorDebugPanel';
import PackageNode from '../../components/nodes/PackageNode/PackageNode';
import { ClassNode } from '../../components/nodes/ClassNode/ClassNode';

// Node types registry
const nodeTypes = {
  package: PackageNode,
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
  const { diagramId: urlDiagramId } = useParams();
  const navigate = useNavigate();
  
  // CRITICAL FIX: Track current diagram ID separately from URL
  // This prevents 409 errors on subsequent saves
  const [currentDiagramId, setCurrentDiagramId] = useState<string | null>(
    urlDiagramId && urlDiagramId !== 'new' ? urlDiagramId : null
  );
  
  // ReactFlow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  // UI state
  const [selectedNode, setSelectedNode] = useState<Node<NodeData> | null>(null);
  const [selectedTool, setSelectedTool] = useState<'select' | 'pan'>('select');
  const [activeTab, setActiveTab] = useState<'elements' | 'hierarchy'>('elements');
  
  // Modal state
  const [showCardinalityModal, setShowCardinalityModal] = useState(false);
  const [showNameModal, setShowNameModal] = useState(false);
  const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null);
  
  // Loading state
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Diagram metadata
  const [diagramName, setDiagramName] = useState('Untitled Diagram');
  const [workspaceName, setWorkspaceName] = useState('default');
  const [graphName, setGraphName] = useState('');
  
  // History for undo/redo
  const [history, setHistory] = useState<Array<{ nodes: Node<NodeData>[]; edges: Edge<EdgeData>[] }>>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  const nodeIdCounter = useRef(1);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  // Update currentDiagramId when URL changes
  useEffect(() => {
    if (urlDiagramId && urlDiagramId !== 'new' && urlDiagramId !== currentDiagramId) {
      setCurrentDiagramId(urlDiagramId);
    }
  }, [urlDiagramId]);

  // Load diagram data
  useEffect(() => {
    if (currentDiagramId) {
      loadDiagram(currentDiagramId);
    }
  }, [currentDiagramId]);

  // Track selection changes
  useEffect(() => {
    const handleSelectionChange = () => {
      if (!reactFlowInstance) return;
      
      const selectedNodes = nodes.filter(node => node.selected);
      if (selectedNodes.length === 1) {
        setSelectedNode(selectedNodes[0]);
      } else {
        setSelectedNode(null);
      }
    };

    handleSelectionChange();
  }, [nodes, reactFlowInstance]);

  // Setup global updateNodeData function
  useEffect(() => {
    window.updateNodeData = (nodeId: string, updates: Partial<NodeData>) => {
      handleNodeUpdate(nodeId, updates);
    };
    
    return () => {
      delete window.updateNodeData;
    };
  }, []);

  // ============================================================================
  // LOAD DIAGRAM
  // ============================================================================

  const loadDiagram = async (id: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.get(`/diagrams/${id}`);
      const diagram = response.data;

      setDiagramName(diagram.name || 'Untitled Diagram');
      setWorkspaceName(diagram.workspace_name || 'default');
      setGraphName(diagram.graph_name || '');

      if (diagram.settings) {
        if (diagram.settings.nodes) {
          setNodes(diagram.settings.nodes);
        }
        if (diagram.settings.edges) {
          setEdges(diagram.settings.edges);
        }
        if (diagram.settings.viewport && reactFlowInstance) {
          reactFlowInstance.setViewport(diagram.settings.viewport);
        }
      }
    } catch (error) {
      console.error('Failed to load diagram:', error);
      alert('Failed to load diagram. Redirecting to home.');
      navigate('/');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // HISTORY (UNDO/REDO)
  // ============================================================================

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

  // ============================================================================
  // NODE OPERATIONS
  // ============================================================================

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

      // Create node WITHOUT default attributes - empty by default
      const newNode: Node<NodeData> = {
        id: `node_${nodeIdCounter.current++}`,
        type: type,
        position,
        data: {
          label: type.charAt(0).toUpperCase() + type.slice(1),
          type: type as any,
          stereotype: '',
          color: ELEMENT_COLORS[type],
          // NO default attributes - users add them via ElementEditor
          attributes: (type === 'class' || type === 'object') ? [] : undefined,
          methods: (type === 'class' || type === 'interface') ? [] : undefined,
          literals: type === 'enumeration' ? [] : undefined,
          // Package-specific properties
          isExpanded: type === 'package' ? true : undefined,
          childCount: type === 'package' ? 0 : undefined,
        } as any,
      };

      setNodes((nds) => nds.concat(newNode));
      saveToHistory();
    },
    [reactFlowInstance, setNodes]
  );

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleNodeUpdate = useCallback(
    (nodeId: string, updates: Partial<NodeData>) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, ...updates } }
            : node
        )
      );
      saveToHistory();
    },
    [setNodes]
  );

  // ============================================================================
  // EDGE OPERATIONS
  // ============================================================================

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
      saveToHistory();
    },
    [pendingConnection, setEdges]
  );

  // ============================================================================
  // SAVE OPERATIONS - FIXED FOR 409 ISSUE
  // ============================================================================

  const handleSave = async () => {
    // CRITICAL FIX: Check currentDiagramId, not urlDiagramId
    if (!currentDiagramId) {
      // First save - show name modal
      setShowNameModal(true);
      return;
    }
    
    // Subsequent saves - update existing diagram
    await performSave(workspaceName, diagramName);
  };

  const performSave = async (workspace: string, name: string) => {
    try {
      setIsSaving(true);

      const viewport = reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 };

      const payload = {
        nodes,
        edges,
        viewport,
      };

      let savedDiagramId: string;
      let savedGraphName: string;

      // CRITICAL FIX: Use currentDiagramId to determine if updating or creating
      const isUpdate = currentDiagramId !== null;
      
      console.log('Save operation:', {
        isUpdate,
        currentDiagramId,
        diagramName: name,
        workspaceName: workspace
      });

      if (isUpdate) {
        // Update existing diagram
        console.log('Updating existing diagram:', currentDiagramId);
        const response = await apiClient.put(`/diagrams/${currentDiagramId}`, payload);
        savedDiagramId = response.data.id;
        savedGraphName = response.data.graph_name;
      } else {
        // Create new diagram
        console.log('Creating new diagram:', name, 'in workspace:', workspace);
        
        const response = await apiClient.post('/diagrams', {
          ...payload,
          name: name,
          workspace_name: workspace,
        });
        
        savedDiagramId = response.data.id;
        savedGraphName = response.data.graph_name;
        
        console.log('Diagram created:', {
          id: savedDiagramId,
          graph_name: savedGraphName
        });
        
        // CRITICAL FIX: Update currentDiagramId immediately
        setCurrentDiagramId(savedDiagramId);
        
        // Update URL
        navigate(`/builder/${savedDiagramId}`, { replace: true });
      }

      // CRITICAL FIX: Update UI state immediately
      setDiagramName(name);
      setWorkspaceName(workspace);
      setGraphName(savedGraphName);

      // Sync to FalkorDB
      if (savedDiagramId && savedGraphName) {
        try {
          console.log('Syncing to FalkorDB:', savedGraphName);
          await apiClient.post(`/diagrams/${savedDiagramId}/sync`, {
            nodes: nodes.map(node => ({
              id: node.id,
              type: node.type,
              position: node.position,
              data: node.data,
            })),
            edges: edges.map(edge => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
              data: edge.data,
            })),
          });
          console.log('✅ Synced to FalkorDB:', savedGraphName);
        } catch (syncError) {
          console.error('FalkorDB sync failed:', syncError);
          // Don't fail the save if sync fails
        }
      }

      alert(`Diagram saved successfully!`);
    } catch (error: any) {
      console.error('Failed to save diagram:', error);
      
      // Better error handling
      if (error.response?.status === 409) {
        alert('A diagram with this name already exists in this workspace. Please try a different name.');
      } else {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        alert(`Failed to save diagram: ${errorMsg}`);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleNameModalSubmit = (workspace: string, name: string) => {
    setShowNameModal(false);
    performSave(workspace, name);
  };

  // ============================================================================
  // PUBLISH OPERATION
  // ============================================================================

  const handlePublish = async () => {
    if (!currentDiagramId) {
      alert('Please save the diagram before publishing.');
      return;
    }

    try {
      setIsPublishing(true);
      await apiClient.post(`/diagrams/${currentDiagramId}/publish`);
      alert('Diagram published successfully!');
    } catch (error) {
      console.error('Failed to publish diagram:', error);
      alert('Failed to publish diagram. Please try again.');
    } finally {
      setIsPublishing(false);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading diagram...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen" style={{ backgroundColor: COLORS.OFF_WHITE }}>
      {/* Left Sidebar */}
      <aside
        className="w-80 border-r-2 flex flex-col"
        style={{ borderColor: COLORS.LIGHT_GREY, backgroundColor: COLORS.WHITE }}
      >
        {/* Header - FIXED: Updates after save */}
        <div className="p-4 border-b-2" style={{ borderColor: COLORS.LIGHT_GREY }}>
          <h2 className="text-xl font-bold" style={{ color: COLORS.BLACK }}>
            {diagramName}
          </h2>
          <p className="text-sm" style={{ color: COLORS.DARK_GREY }}>
            Workspace: {workspaceName}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b" style={{ borderColor: COLORS.LIGHT_GREY }}>
          <button
            onClick={() => setActiveTab('elements')}
            className="flex-1 py-2 text-sm font-medium transition"
            style={{
              backgroundColor: activeTab === 'elements' ? COLORS.PRIMARY : COLORS.OFF_WHITE,
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
        <div className="flex-1 overflow-auto p-4">
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

        {/* Top Toolbar */}
        <div className="absolute top-4 right-4 flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 rounded shadow-lg transition"
            style={{
              backgroundColor: COLORS.SUCCESS,
              color: COLORS.WHITE,
              opacity: isSaving ? 0.6 : 1,
            }}
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handlePublish}
            disabled={isPublishing}
            className="flex items-center gap-2 px-4 py-2 rounded shadow-lg transition"
            style={{
              backgroundColor: COLORS.PRIMARY,
              color: COLORS.WHITE,
              opacity: isPublishing ? 0.6 : 1,
            }}
          >
            <Upload className="w-4 h-4" />
            {isPublishing ? 'Publishing...' : 'Publish'}
          </button>
        </div>

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
            <div className="w-px bg-gray-300"></div>
            <button
              onClick={handleUndo}
              disabled={historyIndex <= 0}
              className="p-3 rounded hover:bg-gray-100 disabled:opacity-30"
              title="Undo"
            >
              <Undo2 className="w-5 h-5" style={{ color: COLORS.BLACK }} />
            </button>
            <button
              onClick={handleRedo}
              disabled={historyIndex >= history.length - 1}
              className="p-3 rounded hover:bg-gray-100 disabled:opacity-30"
              title="Redo"
            >
              <Redo2 className="w-5 h-5" style={{ color: COLORS.BLACK }} />
            </button>
            <div className="w-px bg-gray-300"></div>
            <button
              onClick={() => reactFlowInstance?.zoomIn()}
              className="p-3 rounded hover:bg-gray-100"
              title="Zoom In"
            >
              <ZoomIn className="w-5 h-5" style={{ color: COLORS.BLACK }} />
            </button>
            <button
              onClick={() => reactFlowInstance?.zoomOut()}
              className="p-3 rounded hover:bg-gray-100"
              title="Zoom Out"
            >
              <ZoomOut className="w-5 h-5" style={{ color: COLORS.BLACK }} />
            </button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Element Editor */}
      {selectedNode && (
        <ElementEditor
          selectedNode={selectedNode}
          onUpdate={handleNodeUpdate}
          onClose={() => setSelectedNode(null)}
        />
      )}

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

      {/* Diagram Name Modal */}
      <DiagramNameModal
        isOpen={showNameModal}
        onClose={() => setShowNameModal(false)}
        onSubmit={handleNameModalSubmit}
        defaultWorkspace={workspaceName}
        defaultDiagram={diagramName}
      />

      {/* FalkorDB Debug Panel */}
      {currentDiagramId && graphName && (
        <FalkorDebugPanel 
          diagramId={currentDiagramId} 
          graphName={graphName} 
        />
      )}
    </div>
  );
};

export default OntologyBuilderPage;

// Global type declaration
declare global {
  interface Window {
    updateNodeData?: (nodeId: string, updates: Partial<NodeData>) => void;
  }
}