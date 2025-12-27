// frontend/src/components/edges/er/RelationshipEdge/RelationshipEdge.tsx
import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

export const RelationshipEdge = memo<EdgeProps>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
  style = {},
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

  const cardinality = data?.cardinality || '1:N';
  const label = data?.label || '';

  // Parse cardinality
  const [sourceCard, targetCard] = cardinality.split(':');

  return (
    <>
      <path
        id={id}
        style={{
          ...style,
          strokeWidth: selected ? 3 : 2,
          stroke: selected ? '#3b82f6' : '#6b7280',
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />

      <EdgeLabelRenderer>
        {/* Relationship Label (center) */}
        {label && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            <div className="bg-white px-3 py-1 rounded border border-gray-300 shadow-sm text-xs font-medium text-gray-700">
              {label}
            </div>
          </div>
        )}

        {/* Source Cardinality */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${sourceX + (labelX - sourceX) * 0.15}px,${sourceY + (labelY - sourceY) * 0.15}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <div className="bg-blue-100 px-2 py-0.5 rounded text-xs font-bold text-blue-700 border border-blue-300">
            {sourceCard}
          </div>
        </div>

        {/* Target Cardinality */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${targetX + (labelX - targetX) * 0.15}px,${targetY + (labelY - targetY) * 0.15}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <div className="bg-blue-100 px-2 py-0.5 rounded text-xs font-bold text-blue-700 border border-blue-300">
            {targetCard}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

RelationshipEdge.displayName = 'RelationshipEdge';