import React, { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge as RFBaseEdge } from 'reactflow';

export interface CustomEdgeProps extends EdgeProps {
  label?: string;
  markerEnd?: string;
  markerStart?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  animated?: boolean;
}

export const BaseEdge = memo<CustomEdgeProps>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  markerEnd,
  markerStart,
  strokeWidth = 2,
  strokeDasharray,
  animated = false,
  selected,
  style = {},
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
      <RFBaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        markerStart={markerStart}
        style={{
          ...style,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          stroke: selected ? '#3b82f6' : (style.stroke || '#6b7280'),
          strokeDasharray,
        }}
        className={animated ? 'animated' : ''}
      />
      
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan bg-white px-2 py-1 rounded shadow-sm border border-gray-300 text-xs font-medium text-gray-700"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

BaseEdge.displayName = 'BaseEdge';