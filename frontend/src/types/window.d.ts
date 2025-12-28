// frontend/src/types/window.d.ts

export {};

declare global {
  interface Window {
    updateNodeData?: (nodeId: string, newData: any) => void;
    updateEdgeData?: (edgeId: string, newData: any) => void;
  }
}