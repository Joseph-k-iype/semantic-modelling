// frontend/src/components/diagram/DiagramCanvas/DiagramCanvas.tsx
// COMPLETE IMPLEMENTATION - Fixed TypeScript errors
// Path: frontend/src/components/diagram/DiagramCanvas/DiagramCanvas.tsx

import React, { useCallback, useState, useEffect, useMemo, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  Panel,
  NodeTypes,
  EdgeTypes,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Import API client - FIXED: Use this instead of manual URL construction
import { apiClient } from '../../../services/api/client';

// Import toolbar
import { DiagramToolbar } from '../DiagramToolbar/DiagramToolbar';

// Import node components
import EntityNode from '../../nodes/er/EntityNode/EntityNode';
import ClassNode from '../../nodes/uml/ClassNode/ClassNode';
import LifelineNode from '../../nodes/uml/LifelineNode/LifelineNode';
import TaskNode from '../../nodes/bpmn/TaskNode/TaskNode';
import EventNode from '../../nodes/bpmn/EventNode/EventNode';
import GatewayNode from '../../nodes/bpmn/GatewayNode/GatewayNode';
import PoolNode from '../../nodes/bpmn/PoolNode/PoolNode';

// Import edge components
import RelationshipEdge from '../../edges/er/RelationshipEdge/RelationshipEdge';
import AssociationEdge from '../../edges/uml/AssociationEdge/AssociationEdge';
import MessageEdge from '../../edges/uml/MessageEdge/MessageEdge';
import SequenceFlowEdge from '../../edges/bpmn/SequenceFlowEdge/SequenceFlowEdge';

// Import factory for default data
import { getDefaultNodeData } from '../../../features/diagram-engine/NodeFactory';

interface DiagramCanvasProps {
  modelId: string;
  diagramId: string;
  notation: 'er' | 'uml-class' | 'uml-sequence' | 'bpmn' | 'uml-interaction';
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ modelId, diagramId, notation }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string; edgeId?: string } | null>(null);
  const [maxZIndex, setMaxZIndex] = useState(1);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
  // Track if diagram has unsaved changes
  const hasChangesRef = useRef(false);
  const saveTimeoutRef = useRef<number | null>(null);

  // Define node types
  const nodeTypes: NodeTypes = useMemo(() => ({
    // ER Nodes
    ER_ENTITY: EntityNode,
    ER_WEAK_ENTITY: EntityNode,
    ER_ATTRIBUTE: EntityNode,
    entityNode: EntityNode,

    // UML Nodes
    UML_CLASS: ClassNode,
    UML_INTERFACE: ClassNode,
    UML_ABSTRACT_CLASS: ClassNode,
    UML_PACKAGE: ClassNode,
    UML_COMPONENT: ClassNode,
    classNode: ClassNode,
    
    // UML Sequence Nodes
    UML_LIFELINE: LifelineNode,
    lifelineNode: LifelineNode,

    // BPMN Nodes
    BPMN_TASK: TaskNode,
    BPMN_USER_TASK: TaskNode,
    BPMN_SERVICE_TASK: TaskNode,
    BPMN_MANUAL_TASK: TaskNode,
    BPMN_SCRIPT_TASK: TaskNode,
    taskNode: TaskNode,
    
    BPMN_START_EVENT: EventNode,
    BPMN_END_EVENT: EventNode,
    BPMN_INTERMEDIATE_EVENT: EventNode,
    eventNode: EventNode,
    
    BPMN_GATEWAY_EXCLUSIVE: GatewayNode,
    BPMN_GATEWAY_PARALLEL: GatewayNode,
    BPMN_GATEWAY_INCLUSIVE: GatewayNode,
    gatewayNode: GatewayNode,
    
    BPMN_POOL: PoolNode,
    BPMN_LANE: PoolNode,
    poolNode: PoolNode,
  }), []);

  // Define edge types
  const edgeTypes: EdgeTypes = useMemo(() => ({
    // ER Edges
    ER_RELATIONSHIP: RelationshipEdge,
    ER_ATTRIBUTE_LINK: RelationshipEdge,
    relationshipEdge: RelationshipEdge,

    // UML Edges
    UML_ASSOCIATION: AssociationEdge,
    UML_AGGREGATION: AssociationEdge,
    UML_COMPOSITION: AssociationEdge,
    UML_GENERALIZATION: AssociationEdge,
    UML_DEPENDENCY: AssociationEdge,
    UML_REALIZATION: AssociationEdge,
    associationEdge: AssociationEdge,
    
    // UML Sequence Message Edge
    UML_MESSAGE: MessageEdge,
    messageEdge: MessageEdge,

    // BPMN Edges
    BPMN_SEQUENCE_FLOW: SequenceFlowEdge,
    BPMN_MESSAGE_FLOW: SequenceFlowEdge,
    BPMN_ASSOCIATION: SequenceFlowEdge,
    sequenceFlowEdge: SequenceFlowEdge,
  }), []);

  // Setup global update functions for nodes and edges
  useEffect(() => {
    (window as any).updateNodeData = (nodeId: string, newData: any) => {
      setNodes(nds => nds.map(node => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...newData } };
        }
        return node;
      }));
      markAsChanged();
    };

    (window as any).updateEdgeData = (edgeId: string, newData: any) => {
      setEdges(eds => eds.map(edge => {
        if (edge.id === edgeId) {
          return { ...edge, data: { ...edge.data, ...newData } };
        }
        return edge;
      }));
      markAsChanged();
    };

    return () => {
      delete (window as any).updateNodeData;
      delete (window as any).updateEdgeData;
    };
  }, [setNodes, setEdges]);

  // Load diagram data on mount
  useEffect(() => {
    loadDiagramData();
  }, [modelId, diagramId]);

  // Auto-save when changes detected
  useEffect(() => {
    if (hasChangesRef.current && nodes.length > 0) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      
      // Set new timeout for auto-save (2 seconds after last change)
      saveTimeoutRef.current = setTimeout(() => {
        saveDiagram();
      }, 2000);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [nodes, edges]);

  // Mark diagram as changed
  const markAsChanged = useCallback(() => {
    hasChangesRef.current = true;
  }, []);

  // Load diagram data from backend - FIXED: Use apiClient
  const loadDiagramData = async () => {
    try {
      const response = await apiClient.get(`/diagrams/${diagramId}`);
      const data = response.data;
      
      // The backend stores nodes and edges in the diagram
      if (data.nodes && Array.isArray(data.nodes)) {
        setNodes(data.nodes);
      }
      if (data.edges && Array.isArray(data.edges)) {
        setEdges(data.edges);
      }
      console.log('Diagram loaded:', data);
    } catch (error) {
      console.error('Failed to load diagram:', error);
    }
  };

  // Save entire diagram to backend - FIXED: Use apiClient
  const saveDiagram = async () => {
    if (isSaving) return;
    
    setIsSaving(true);
    try {
      // Prepare diagram data
      const diagramData = {
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: node.data,
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          type: edge.type,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
          data: edge.data,
        })),
        viewport: reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 },
      };

      const response = await apiClient.patch(`/diagrams/${diagramId}`, {
        notation_config: diagramData,
      });

      if (response.status === 200) {
        hasChangesRef.current = false;
        setLastSaved(new Date());
        console.log('Diagram saved successfully');
      } else {
        console.error('Failed to save diagram');
      }
    } catch (error) {
      console.error('Error saving diagram:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle drop from toolbar
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      
      if (typeof type === 'undefined' || !type || !reactFlowInstance) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: `${type.toLowerCase()}-${Date.now()}`,
        type,
        position,
        data: getDefaultNodeData(type, position),
      };

      setNodes((nds) => nds.concat(newNode));
      markAsChanged();
    },
    [reactFlowInstance, setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle connection - FIXED: Type guard for source and target
  const onConnect = useCallback((params: Connection) => {
    // FIXED: Add type guard to ensure source and target are not null
    if (!params.source || !params.target) {
      console.warn('Connection missing source or target');
      return;
    }

    // Determine edge type based on notation
    let edgeType = 'default';
    let edgeData: any = {};
    
    if (notation === 'er') {
      edgeType = 'relationshipEdge';
      edgeData = {
        label: '',
        sourceCardinality: '1',
        targetCardinality: 'N'
      };
    } else if (notation === 'uml-class' || notation === 'uml-interaction') {
      edgeType = 'associationEdge';
      edgeData = {
        label: '',
        associationType: 'association',
        sourceMultiplicity: '1',
        targetMultiplicity: '1'
      };
    } else if (notation === 'uml-sequence') {
      edgeType = 'messageEdge';
      edgeData = {
        label: 'message()',
        messageType: 'sync'
      };
    } else if (notation === 'bpmn') {
      edgeType = 'sequenceFlowEdge';
      edgeData = {
        label: '',
        isDefault: false
      };
    }

    // FIXED: Properly typed edge with non-null source and target
    const newEdge: Edge = {
      id: `edge-${Date.now()}`,
      source: params.source,
      target: params.target,
      sourceHandle: params.sourceHandle,
      targetHandle: params.targetHandle,
      type: edgeType,
      data: edgeData
    };

    setEdges((eds) => addEdge(newEdge, eds));
    markAsChanged();
  }, [notation, setEdges]);

  // Wrap onNodesChange to mark as changed
  const handleNodesChange = useCallback((changes: any) => {
    onNodesChange(changes);
    markAsChanged();
  }, [onNodesChange]);

  // Wrap onEdgesChange to mark as changed
  const handleEdgesChange = useCallback((changes: any) => {
    onEdgesChange(changes);
    markAsChanged();
  }, [onEdgesChange]);

  // Handle node selection
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  // Handle edge selection
  const onEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
  }, []);

  // Handle context menu
  const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      nodeId: node.id
    });
  }, []);

  const onEdgeContextMenu = useCallback((event: React.MouseEvent, edge: Edge) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      edgeId: edge.id
    });
  }, []);

  // Delete element from context menu
  const deleteElement = useCallback(() => {
    if (contextMenu?.nodeId) {
      setNodes(nds => nds.filter(node => node.id !== contextMenu.nodeId));
      setEdges(eds => eds.filter(edge => 
        edge.source !== contextMenu.nodeId && edge.target !== contextMenu.nodeId
      ));
      markAsChanged();
    } else if (contextMenu?.edgeId) {
      setEdges(eds => eds.filter(edge => edge.id !== contextMenu.edgeId));
      markAsChanged();
    }
    setContextMenu(null);
  }, [contextMenu, setNodes, setEdges]);

  // Z-index management
  const bringToFront = useCallback((nodeId?: string, edgeId?: string) => {
    const newZIndex = maxZIndex + 1;
    setMaxZIndex(newZIndex);

    if (nodeId) {
      setNodes(nds => nds.map(node => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, zIndex: newZIndex } };
        }
        return node;
      }));
    } else if (edgeId) {
      setEdges(eds => eds.map(edge => {
        if (edge.id === edgeId) {
          return { ...edge, data: { ...edge.data, zIndex: newZIndex } };
        }
        return edge;
      }));
    }

    setContextMenu(null);
    markAsChanged();
  }, [maxZIndex, setNodes, setEdges]);

  const sendToBack = useCallback((nodeId?: string, edgeId?: string) => {
    if (nodeId) {
      setNodes(nds => nds.map(node => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, zIndex: 0 } };
        }
        return node;
      }));
    } else if (edgeId) {
      setEdges(eds => eds.map(edge => {
        if (edge.id === edgeId) {
          return { ...edge, data: { ...edge.data, zIndex: 0 } };
        }
        return edge;
      }));
    }

    setContextMenu(null);
    markAsChanged();
  }, [setNodes, setEdges]);

  // Update node color
  const updateNodeColor = useCallback((color: string) => {
    if (selectedNode) {
      setNodes(nds => nds.map(node => {
        if (node.id === selectedNode.id) {
          return {
            ...node,
            data: { ...node.data, color }
          };
        }
        return node;
      }));
      markAsChanged();
    }
  }, [selectedNode, setNodes]);

  // Update edge color
  const updateEdgeColor = useCallback((color: string) => {
    if (selectedEdge) {
      setEdges(eds => eds.map(edge => {
        if (edge.id === selectedEdge.id) {
          return {
            ...edge,
            data: { ...edge.data, color }
          };
        }
        return edge;
      }));
      markAsChanged();
    }
  }, [selectedEdge, setEdges]);

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
    setContextMenu(null);
  }, []);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', display: 'flex' }}>
      {/* Toolbar */}
      <DiagramToolbar />
      
      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onNodeContextMenu={onNodeContextMenu}
          onEdgeContextMenu={onEdgeContextMenu}
          onPaneClick={onPaneClick}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          snapToGrid
          snapGrid={[15, 15]}
        >
          <Background />
          <Controls />
          <MiniMap />

          {/* Save Status Indicator */}
          <Panel position="top-left">
            <div style={{
              background: 'white',
              padding: '8px 12px',
              borderRadius: '6px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              fontSize: '12px',
              color: '#666',
            }}>
              {isSaving ? (
                <span>💾 Saving...</span>
              ) : lastSaved ? (
                <span>✓ Saved {lastSaved.toLocaleTimeString()}</span>
              ) : (
                <span>Ready</span>
              )}
            </div>
          </Panel>

          {/* Properties Panel */}
          {(selectedNode || selectedEdge) && (
            <Panel position="top-right">
              <div
                style={{
                  background: 'white',
                  padding: '12px',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                  minWidth: '200px'
                }}
              >
                <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 'bold' }}>
                  {selectedNode ? 'Node Properties' : 'Edge Properties'}
                </h3>
                
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                    Color:
                  </label>
                  <input
                    type="color"
                    value={selectedNode?.data?.color || selectedEdge?.data?.color || '#ffffff'}
                    onChange={(e) => selectedNode ? updateNodeColor(e.target.value) : updateEdgeColor(e.target.value)}
                    style={{ width: '100%', height: '32px' }}
                  />
                </div>

                {selectedNode && (
                  <div>
                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                      Text Color:
                    </label>
                    <input
                      type="color"
                      value={selectedNode?.data?.textColor || '#000000'}
                      onChange={(e) => {
                        setNodes(nds => nds.map(node => {
                          if (node.id === selectedNode.id) {
                            return {
                              ...node,
                              data: { ...node.data, textColor: e.target.value }
                            };
                          }
                          return node;
                        }));
                        markAsChanged();
                      }}
                      style={{ width: '100%', height: '32px' }}
                    />
                  </div>
                )}
              </div>
            </Panel>
          )}
        </ReactFlow>

        {/* Context Menu */}
        {contextMenu && (
          <>
            <div
              style={{
                position: 'fixed',
                top: contextMenu.y,
                left: contextMenu.x,
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                zIndex: 1000
              }}
            >
              <button
                onClick={() => bringToFront(contextMenu.nodeId, contextMenu.edgeId)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '8px 16px',
                  border: 'none',
                  background: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
              >
                Bring to Front
              </button>
              <button
                onClick={() => sendToBack(contextMenu.nodeId, contextMenu.edgeId)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '8px 16px',
                  border: 'none',
                  background: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
              >
                Send to Back
              </button>
              <hr style={{ margin: '4px 0', border: 'none', borderTop: '1px solid #e5e7eb' }} />
              <button
                onClick={deleteElement}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '8px 16px',
                  border: 'none',
                  background: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '13px',
                  color: '#dc2626'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#fee2e2'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
              >
                Delete
              </button>
            </div>
            
            {/* Click outside to close context menu */}
            <div
              onClick={() => setContextMenu(null)}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 999
              }}
            />
          </>
        )}
      </div>
    </div>
  );
};

export default DiagramCanvas;