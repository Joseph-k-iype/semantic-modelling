// frontend/src/components/edges/bpmn/BPMNEdges.tsx
import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

// Sequence Flow Edge (solid line with arrow)
export const SequenceFlowEdge = memo<EdgeProps>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <defs>
        <marker
          id={`sequence-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill={selected ? '#10b981' : '#6b7280'}
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#10b981' : '#6b7280'}
        markerEnd={`url(#sequence-${id})`}
      />
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
            className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700 border border-gray-300 shadow-sm"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

// Message Flow Edge (dashed line with hollow arrow)
export const MessageFlowEdge = memo<EdgeProps>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <defs>
        <marker
          id={`message-flow-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill="white"
            stroke={selected ? '#10b981' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#10b981' : '#6b7280'}
        strokeDasharray="5,5"
        markerEnd={`url(#message-flow-${id})`}
      />
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
            className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700 border border-gray-300 shadow-sm"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

// Association Edge (dotted line)
export const BPMNAssociationEdge = memo<EdgeProps>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#10b981' : '#6b7280'}
        strokeDasharray="2,2"
      />
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
            className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700 border border-gray-300 shadow-sm"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

// Set display names
SequenceFlowEdge.displayName = 'SequenceFlowEdge';
MessageFlowEdge.displayName = 'MessageFlowEdge';
BPMNAssociationEdge.displayName = 'BPMNAssociationEdge';