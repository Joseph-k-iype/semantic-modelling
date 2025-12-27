import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { 
  Node, 
  Edge, 
  addEdge, 
  applyNodeChanges, 
  applyEdgeChanges,
  Connection,
  NodeChange,
  EdgeChange,
  XYPosition
} from 'reactflow';
import { DiagramType, DiagramNode, DiagramEdge } from '../types/diagram.types';
import { createDefaultNodeData } from '../features/diagram-engine/NodeFactory';

interface DiagramState {
  // Current diagram
  diagramId: string | null;
  diagramName: string;
  diagramType: DiagramType;
  modelId: string | null;
  workspaceId: string | null;

  // Nodes and edges
  nodes: DiagramNode[];
  edges: DiagramEdge[];

  // Selection
  selectedNodeIds: string[];
  selectedEdgeIds: string[];

  // Viewport
  viewport: { x: number; y: number; zoom: number };

  // UI State
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  isDirty: boolean;

  // Actions
  setDiagram: (diagram: {
    id: string;
    name: string;
    type: DiagramType;
    modelId: string;
    workspaceId: string;
    nodes: DiagramNode[];
    edges: DiagramEdge[];
    viewport?: { x: number; y: number; zoom: number };
  }) => void;
  
  setDiagramType: (type: DiagramType) => void;
  
  // Node operations
  addNode: (nodeType: string, position: XYPosition) => void;
  updateNode: (nodeId: string, data: Partial<any>) => void;
  deleteNode: (nodeId: string) => void;
  onNodesChange: (changes: NodeChange[]) => void;

  // Edge operations
  addEdge: (connection: Connection) => void;
  updateEdge: (edgeId: string, data: Partial<any>) => void;
  deleteEdge: (edgeId: string) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;

  // Selection operations
  setSelectedNodes: (nodeIds: string[]) => void;
  setSelectedEdges: (edgeIds: string[]) => void;
  clearSelection: () => void;

  // Viewport operations
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;

  // Persistence operations
  saveDiagram: () => Promise<void>;
  loadDiagram: (diagramId: string) => Promise<void>;
  
  // Reset
  resetDiagram: () => void;
}

const initialState = {
  diagramId: null,
  diagramName: 'Untitled Diagram',
  diagramType: DiagramType.UML_CLASS,
  modelId: null,
  workspaceId: null,
  nodes: [],
  edges: [],
  selectedNodeIds: [],
  selectedEdgeIds: [],
  viewport: { x: 0, y: 0, zoom: 1 },
  isLoading: false,
  isSaving: false,
  error: null,
  isDirty: false,
};

export const useDiagramStore = create<DiagramState>()(
  immer((set, get) => ({
    ...initialState,

    setDiagram: (diagram) => {
      set((state) => {
        state.diagramId = diagram.id;
        state.diagramName = diagram.name;
        state.diagramType = diagram.type;
        state.modelId = diagram.modelId;
        state.workspaceId = diagram.workspaceId;
        state.nodes = diagram.nodes;
        state.edges = diagram.edges;
        state.viewport = diagram.viewport || initialState.viewport;
        state.isDirty = false;
      });
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
        data: createDefaultNodeData(nodeType, position),
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

    clearSelection: () => {
      set((state) => {
        state.selectedNodeIds = [];
        state.selectedEdgeIds = [];
      });
    },

    setViewport: (viewport) => {
      set((state) => {
        state.viewport = viewport;
      });
    },

    saveDiagram: async () => {
      set((state) => {
        state.isSaving = true;
        state.error = null;
      });

      try {
        const state = get();
        const diagramData = {
          id: state.diagramId,
          name: state.diagramName,
          type: state.diagramType,
          modelId: state.modelId,
          workspaceId: state.workspaceId,
          nodes: state.nodes,
          edges: state.edges,
          viewport: state.viewport,
        };

        // TODO: Call API to save diagram
        console.log('Saving diagram:', diagramData);

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

    loadDiagram: async (diagramId) => {
      set((state) => {
        state.isLoading = true;
        state.error = null;
      });

      try {
        // TODO: Call API to load diagram
        console.log('Loading diagram:', diagramId);

        set((state) => {
          state.isLoading = false;
        });
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to load diagram';
          state.isLoading = false;
        });
      }
    },

    resetDiagram: () => {
      set(initialState);
    },
  }))
);