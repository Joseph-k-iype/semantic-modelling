import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import {
  Edge,
  Connection,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  addEdge,
} from 'reactflow';
import { DiagramNode, DiagramType } from '../types/diagram.types';
import { getDefaultNodeData } from '../features/diagram-engine/NodeFactory';

interface DiagramStore {
  // State
  diagramId: string;
  diagramName: string;
  diagramType: DiagramType;
  nodes: DiagramNode[];
  edges: Edge[];
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  viewport: { x: number; y: number; zoom: number };
  isDirty: boolean;
  isSaving: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setDiagram: (diagram: Partial<DiagramStore>) => void;
  loadDiagram: (diagramId: string) => Promise<void>;
  saveDiagram: () => Promise<void>;
  setDiagramType: (type: DiagramType) => void;
  
  // Node actions
  addNode: (nodeType: string, position: { x: number; y: number }) => void;
  updateNode: (nodeId: string, data: any) => void;
  deleteNode: (nodeId: string) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  
  // Edge actions
  addEdge: (connection: Connection) => void;
  updateEdge: (edgeId: string, data: any) => void;
  deleteEdge: (edgeId: string) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  
  // Selection actions
  setSelectedNodes: (nodeIds: string[]) => void;
  setSelectedEdges: (edgeIds: string[]) => void;
  
  // Viewport actions
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;
}

export const useDiagramStore = create<DiagramStore>()(
  immer((set, get) => ({
    // Initial state
    diagramId: '',
    diagramName: 'Untitled Diagram',
    diagramType: DiagramType.UML_CLASS,
    nodes: [],
    edges: [],
    selectedNodeIds: [],
    selectedEdgeIds: [],
    viewport: { x: 0, y: 0, zoom: 1 },
    isDirty: false,
    isSaving: false,
    isLoading: false,
    error: null,

    // Actions
    setDiagram: (diagram) => {
      set((state) => {
        Object.assign(state, diagram);
      });
    },

    loadDiagram: async (diagramId) => {
      set((state) => {
        state.isLoading = true;
        state.error = null;
      });

      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/diagrams/${diagramId}`);
        // const data = await response.json();
        
        // Mock data for now
        const mockData = {
          id: diagramId,
          name: 'Sample Diagram',
          type: DiagramType.UML_CLASS,
          nodes: [],
          edges: [],
          viewport: { x: 0, y: 0, zoom: 1 },
        };

        set((state) => {
          state.diagramId = mockData.id;
          state.diagramName = mockData.name;
          state.diagramType = mockData.type;
          state.nodes = mockData.nodes;
          state.edges = mockData.edges;
          state.viewport = mockData.viewport;
          state.isLoading = false;
          state.isDirty = false;
        });
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to load diagram';
          state.isLoading = false;
        });
      }
    },

    saveDiagram: async () => {
      set((state) => {
        state.isSaving = true;
        state.error = null;
      });

      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/diagrams/${currentState.diagramId}`, {
        //   method: 'PUT',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({
        //     name: currentState.diagramName,
        //     type: currentState.diagramType,
        //     nodes: currentState.nodes,
        //     edges: currentState.edges,
        //     viewport: currentState.viewport,
        //   }),
        // });

        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));

        set((state) => {
          state.isDirty = false;
          state.isSaving = false;
        });
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to save diagram';
          state.isSaving = false;
        });
      }
    },

    setDiagramType: (type) => {
      set((state) => {
        state.diagramType = type;
        state.isDirty = true;
      });
    },

    addNode: (nodeType, position) => {
      const newNode: DiagramNode = {
        id: `node_${Date.now()}`,
        type: nodeType,
        position,
        data: getDefaultNodeData(nodeType, position),
      };

      set((state) => {
        state.nodes.push(newNode);
        state.isDirty = true;
      });
    },

    updateNode: (nodeId, data) => {
      set((state) => {
        const node = state.nodes.find((n) => n.id === nodeId);
        if (node) {
          node.data = { ...node.data, ...data };
          state.isDirty = true;
        }
      });
    },

    deleteNode: (nodeId) => {
      set((state) => {
        state.nodes = state.nodes.filter((n) => n.id !== nodeId);
        state.edges = state.edges.filter(
          (e) => e.source !== nodeId && e.target !== nodeId
        );
        state.selectedNodeIds = state.selectedNodeIds.filter((id) => id !== nodeId);
        state.isDirty = true;
      });
    },

    onNodesChange: (changes) => {
      set((state) => {
        state.nodes = applyNodeChanges(changes, state.nodes) as DiagramNode[];
        state.isDirty = true;
      });
    },

    addEdge: (connection) => {
      // Determine edge type based on diagram type
      let edgeType = 'default';
      const diagramType = get().diagramType;

      if (diagramType === DiagramType.ER) {
        edgeType = 'ER_RELATIONSHIP';
      } else if (diagramType.startsWith('UML')) {
        edgeType = 'UML_ASSOCIATION';
      } else if (diagramType === DiagramType.BPMN) {
        edgeType = 'BPMN_SEQUENCE_FLOW';
      }

      const newEdge: Edge = {
        ...connection,
        id: `edge_${Date.now()}`,
        type: edgeType,
        data: { label: '' },
      } as Edge;

      set((state) => {
        state.edges = addEdge(newEdge, state.edges);
        state.isDirty = true;
      });
    },

    updateEdge: (edgeId, data) => {
      set((state) => {
        const edge = state.edges.find((e) => e.id === edgeId);
        if (edge) {
          edge.data = { ...edge.data, ...data };
          state.isDirty = true;
        }
      });
    },

    deleteEdge: (edgeId) => {
      set((state) => {
        state.edges = state.edges.filter((e) => e.id !== edgeId);
        state.selectedEdgeIds = state.selectedEdgeIds.filter((id) => id !== edgeId);
        state.isDirty = true;
      });
    },

    onEdgesChange: (changes) => {
      set((state) => {
        state.edges = applyEdgeChanges(changes, state.edges);
        state.isDirty = true;
      });
    },

    setSelectedNodes: (nodeIds) => {
      set((state) => {
        state.selectedNodeIds = nodeIds;
      });
    },

    setSelectedEdges: (edgeIds) => {
      set((state) => {
        state.selectedEdgeIds = edgeIds;
      });
    },

    setViewport: (viewport) => {
      set((state) => {
        state.viewport = viewport;
      });
    },
  }))
);