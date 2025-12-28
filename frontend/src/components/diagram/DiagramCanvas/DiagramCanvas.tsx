// frontend/src/components/diagram/DiagramCanvas/DiagramCanvas.tsx

import React, { useCallback, useState, useEffect, useMemo } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';

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

  // Define node types
  const nodeTypes: NodeTypes = useMemo(() => ({
    entityNode: EntityNode,
    classNode: ClassNode,
    lifelineNode: LifelineNode,
    taskNode: TaskNode,
    eventNode: EventNode,
    gatewayNode: GatewayNode,
    poolNode: PoolNode
  }), []);

  // Define edge types
  const edgeTypes: EdgeTypes = useMemo(() => ({
    relationshipEdge: RelationshipEdge,
    associationEdge: AssociationEdge,
    messageEdge: MessageEdge,
    sequenceFlowEdge: SequenceFlowEdge
  }), []);

  // Setup global update functions for nodes and edges
  useEffect(() => {
    (window as any).updateNodeData = (nodeId: string, newData: any) => {
      setNodes(nds => nds.map(node => {
        if (node.id === nodeId) {
          const updatedNode = { ...node, data: { ...node.data, ...newData } };
          syncNodeToGraph(updatedNode);
          return updatedNode;
        }
        return node;
      }));
    };

    (window as any).updateEdgeData = (edgeId: string, newData: any) => {
      setEdges(eds => eds.map(edge => {
        if (edge.id === edgeId) {
          const updatedEdge = { ...edge, data: { ...edge.data, ...newData } };
          syncEdgeToGraph(updatedEdge);
          return updatedEdge;
        }
        return edge;
      }));
    };

    return () => {
      delete (window as any).updateNodeData;
      delete (window as any).updateEdgeData;
    };
  }, [setNodes, setEdges]);

  // Load diagram data
  useEffect(() => {
    loadDiagramData();
  }, [modelId, diagramId]);

  const loadDiagramData = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/models/${modelId}/diagrams/${diagramId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      }
    } catch (error) {
      console.error('Failed to load diagram:', error);
    }
  };

  // Sync node to graph database
  const syncNodeToGraph = async (node: Node) => {
    try {
      await fetch(
        `${import.meta.env.VITE_API_URL}/models/${modelId}/diagrams/${diagramId}/nodes/${node.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            type: node.type,
            position: node.position,
            data: node.data,
            notation
          })
        }
      );
    } catch (error) {
      console.error('Failed to sync node to graph:', error);
    }
  };

  // Sync edge to graph database
  const syncEdgeToGraph = async (edge: Edge) => {
    try {
      await fetch(
        `${import.meta.env.VITE_API_URL}/models/${modelId}/diagrams/${diagramId}/edges/${edge.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            source: edge.source,
            target: edge.target,
            type: edge.type,
            data: edge.data,
            notation
          })
        }
      );
    } catch (error) {
      console.error('Failed to sync edge to graph:', error);
    }
  };

  // Handle connection
  const onConnect = useCallback((params: Connection) => {
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

    const newEdge = {
      ...params,
      id: `edge-${Date.now()}`,
      type: edgeType,
      data: edgeData
    };

    setEdges((eds) => addEdge(newEdge, eds));
    syncEdgeToGraph(newEdge as Edge);
  }, [notation, setEdges]);

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
  }, [setNodes, setEdges]);

  // Update node color
  const updateNodeColor = useCallback((color: string) => {
    if (selectedNode) {
      setNodes(nds => nds.map(node => {
        if (node.id === selectedNode.id) {
          const updatedNode = {
            ...node,
            data: { ...node.data, color }
          };
          syncNodeToGraph(updatedNode);
          return updatedNode;
        }
        return node;
      }));
    }
  }, [selectedNode, setNodes]);

  // Update edge color
  const updateEdgeColor = useCallback((color: string) => {
    if (selectedEdge) {
      setEdges(eds => eds.map(edge => {
        if (edge.id === selectedEdge.id) {
          const updatedEdge = {
            ...edge,
            data: { ...edge.data, color }
          };
          syncEdgeToGraph(updatedEdge);
          return updatedEdge;
        }
        return edge;
      }));
    }
  }, [selectedEdge, setEdges]);

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
    setContextMenu(null);
  }, []);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onNodeContextMenu={onNodeContextMenu}
        onEdgeContextMenu={onEdgeContextMenu}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />

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
                          const updatedNode = {
                            ...node,
                            data: { ...node.data, textColor: e.target.value }
                          };
                          syncNodeToGraph(updatedNode);
                          return updatedNode;
                        }
                        return node;
                      }));
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
  );
};

export default DiagramCanvas;