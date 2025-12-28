// frontend/src/components/edges/uml/MessageEdge/MessageEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getStraightPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export type MessageType = 'sync' | 'async' | 'return' | 'create' | 'delete';

export interface MessageEdgeData {
  label?: string;
  messageType: MessageType;
  sequence?: number;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const MessageEdge: React.FC<EdgeProps<MessageEdgeData>> = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  selected
}) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data?.label || '');

  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const messageType = data?.messageType || 'sync';
  const edgeColor = data?.color || (selected ? '#3b82f6' : '#000000');
  const strokeWidth = data?.strokeWidth || 2;

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label, 
        messageType: data?.messageType,
        sequence: data?.sequence
      });
    }
  }, [id, label, data?.messageType, data?.sequence]);

  const getStrokeStyle = () => {
    switch (messageType) {
      case 'return':
        return '5,5';
      case 'create':
        return '5,5';
      default:
        return undefined;
    }
  };

  const getMarkerEnd = () => {
    const arrowSize = 10;
    
    switch (messageType) {
      case 'sync':
        // Filled arrow
        return (
          <marker
            id={`sync-message-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polygon
              points={`0,0 ${arrowSize},${arrowSize / 2} 0,${arrowSize}`}
              fill={edgeColor}
            />
          </marker>
        );
      case 'async':
        // Open arrow
        return (
          <marker
            id={`async-message-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polyline
              points={`0,0 ${arrowSize},${arrowSize / 2} 0,${arrowSize}`}
              fill="none"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      case 'return':
        // Open arrow (dashed line)
        return (
          <marker
            id={`return-message-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polyline
              points={`0,0 ${arrowSize},${arrowSize / 2} 0,${arrowSize}`}
              fill="none"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      case 'create':
        // Open arrow with dashed line
        return (
          <marker
            id={`create-message-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polyline
              points={`0,0 ${arrowSize},${arrowSize / 2} 0,${arrowSize}`}
              fill="none"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      case 'delete':
        // X marker
        return (
          <marker
            id={`delete-message-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <path
              d={`M 0 0 L ${arrowSize} ${arrowSize} M 0 ${arrowSize} L ${arrowSize} 0`}
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      default:
        return null;
    }
  };

  return (
    <>
      <defs>
        {getMarkerEnd()}
      </defs>
      
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={`url(#${messageType}-message-${id})`}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          strokeDasharray: getStrokeStyle(),
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Sequence Number */}
        {data?.sequence && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${sourceX + 15}px, ${sourceY}px)`,
              pointerEvents: 'none',
              zIndex: data?.zIndex || 1
            }}
          >
            <div
              style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: 'white',
                border: '2px solid #3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                fontWeight: 'bold'
              }}
            >
              {data.sequence}
            </div>
          </div>
        )}

        {/* Message Label */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 15}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
          onDoubleClick={() => setIsEditingLabel(true)}
        >
          {isEditingLabel ? (
            <input
              type="text"
              value={label}
              onChange={handleLabelChange}
              onBlur={handleLabelBlur}
              autoFocus
              style={{
                padding: '2px 6px',
                fontSize: '11px',
                border: '1px solid #3b82f6',
                borderRadius: '3px',
                outline: 'none',
                minWidth: '80px',
                background: 'white'
              }}
            />
          ) : (
            <div
              style={{
                padding: '2px 6px',
                background: 'white',
                border: `1px solid ${selected ? '#3b82f6' : 'transparent'}`,
                borderRadius: '3px',
                fontSize: '11px',
                cursor: 'text',
                minWidth: '60px',
                textAlign: 'center',
                fontFamily: 'monospace'
              }}
            >
              {label || 'message()'}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

MessageEdge.displayName = 'MessageEdge';

export default MessageEdge;