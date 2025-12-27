// frontend/src/components/edges/uml/UMLEdges.tsx
import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

// Association Edge (solid line)
export const AssociationEdge = memo<EdgeProps>(({
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
        stroke={selected ? '#8b5cf6' : '#6b7280'}
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

// Generalization Edge (solid line with hollow triangle)
export const GeneralizationEdge = memo<EdgeProps>(({
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
          id={`generalization-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill="white"
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        markerEnd={`url(#generalization-${id})`}
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

// Dependency Edge (dashed line with arrow)
export const DependencyEdge = memo<EdgeProps>(({
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
          id={`dependency-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15"
            fill="none"
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        strokeDasharray="5,5"
        markerEnd={`url(#dependency-${id})`}
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

// Aggregation Edge (hollow diamond)
export const AggregationEdge = memo<EdgeProps>(({
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
          id={`aggregation-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 10 L 5 5 L 10 10 L 5 15 Z"
            fill="white"
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        markerStart={`url(#aggregation-${id})`}
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

// Composition Edge (filled diamond)
export const CompositionEdge = memo<EdgeProps>(({
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
          id={`composition-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 10 L 5 5 L 10 10 L 5 15 Z"
            fill={selected ? '#8b5cf6' : '#6b7280'}
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        markerStart={`url(#composition-${id})`}
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

// Realization Edge (dashed line with hollow triangle)
export const RealizationEdge = memo<EdgeProps>(({
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
          id={`realization-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill="white"
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        strokeDasharray="5,5"
        markerEnd={`url(#realization-${id})`}
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

// Message Edge (solid line with arrow)
export const MessageEdge = memo<EdgeProps>(({
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
          id={`message-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15"
            fill="none"
            stroke={selected ? '#8b5cf6' : '#6b7280'}
            strokeWidth="2"
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        markerEnd={`url(#message-${id})`}
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

// Transition Edge (solid line with arrow)
export const TransitionEdge = memo<EdgeProps>(({
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
          id={`transition-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill={selected ? '#8b5cf6' : '#6b7280'}
          />
        </marker>
      </defs>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? '#8b5cf6' : '#6b7280'}
        markerEnd={`url(#transition-${id})`}
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
AssociationEdge.displayName = 'AssociationEdge';
GeneralizationEdge.displayName = 'GeneralizationEdge';
DependencyEdge.displayName = 'DependencyEdge';
AggregationEdge.displayName = 'AggregationEdge';
CompositionEdge.displayName = 'CompositionEdge';
RealizationEdge.displayName = 'RealizationEdge';
MessageEdge.displayName = 'MessageEdge';
TransitionEdge.displayName = 'TransitionEdge';