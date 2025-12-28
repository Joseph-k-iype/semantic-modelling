// frontend/src/components/edges/uml/MessageEdge/MessageEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getStraightPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export type MessageType = 'synchronous' | 'asynchronous' | 'return' | 'create' | 'destroy';

export interface MessageEdgeData {
  label?: string;
  messageType: MessageType;
  sequenceNumber?: string;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const MessageEdge: React.FC<EdgeProps<MessageEdgeData>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected
}) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data?.label || '');
  const [messageType, setMessageType] = useState<MessageType>(data?.messageType || 'synchronous');

  // Use straight path for sequence diagrams
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, messageType });
    }
  }, [id, label, messageType]);

  const handleMessageTypeChange = useCallback((type: MessageType) => {
    setMessageType(type);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, messageType: type });
    }
  }, [id, label]);

  const edgeColor = data?.color || '#000000';
  const strokeWidth = data?.strokeWidth || 2;

  // Get stroke style based on message type
  const getStrokeStyle = () => {
    if (messageType === 'return' || messageType === 'asynchronous') {
      return '5,5'; // dashed
    }
    return undefined;
  };

  // Get marker end based on message type
  const getMarkerEnd = () => {
    const arrowSize = 10;
    
    switch (messageType) {
      case 'synchronous':
        // Filled arrow
        return (
          <marker
            id={`sync-${id}`}
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
      case 'asynchronous':
        // Open arrow
        return (
          <marker
            id={`async-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize}
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
        // Open arrow dashed
        return (
          <marker
            id={`return-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize}
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
        // Filled arrow with "create" stereotype
        return (
          <marker
            id={`create-${id}`}
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
      case 'destroy':
        // X marker
        return (
          <marker
            id={`destroy-${id}`}
            markerWidth={arrowSize * 2}
            markerHeight={arrowSize * 2}
            refX={arrowSize}
            refY={arrowSize}
            orient="auto"
          >
            <line x1="0" y1="0" x2={arrowSize * 2} y2={arrowSize * 2} stroke={edgeColor} strokeWidth={strokeWidth} />
            <line x1={arrowSize * 2} y1="0" x2="0" y2={arrowSize * 2} stroke={edgeColor} strokeWidth={strokeWidth} />
          </marker>
        );
      default:
        return undefined;
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
        markerEnd={`url(#${messageType}-${id})`}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          strokeDasharray: getStrokeStyle(),
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Sequence Number */}
        {data?.sequenceNumber && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${sourceX + 20}px, ${sourceY - 15}px)`,
              pointerEvents: 'none',
              fontSize: '10px',
              fontWeight: 'bold',
              color: edgeColor,
              zIndex: data?.zIndex || 1
            }}
          >
            {data.sequenceNumber}.
          </div>
        )}

        {/* Message Type Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 25}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={messageType}
            onChange={(e) => handleMessageTypeChange(e.target.value as MessageType)}
            style={{
              padding: '2px 4px',
              fontSize: '10px',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              cursor: 'pointer'
            }}
          >
            <option value="synchronous">Synchronous</option>
            <option value="asynchronous">Asynchronous</option>
            <option value="return">Return</option>
            <option value="create">Create</option>
            <option value="destroy">Destroy</option>
          </select>
        </div>

        {/* Message Label */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + 5}px)`,
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
              placeholder="message()"
              style={{
                padding: '2px 6px',
                fontSize: '11px',
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '3px',
                minWidth: '100px',
                fontFamily: 'monospace'
              }}
            />
          ) : (
            <div
              style={{
                padding: '2px 6px',
                fontSize: '11px',
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '3px',
                cursor: 'text',
                fontFamily: 'monospace',
                minWidth: '60px',
                textAlign: 'center'
              }}
            >
              {label || 'message()'}
            </div>
          )}
        </div>

        {/* Create stereotype label */}
        {messageType === 'create' && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 40}px)`,
              pointerEvents: 'none',
              fontSize: '10px',
              fontStyle: 'italic',
              color: edgeColor,
              zIndex: data?.zIndex || 1
            }}
          >
            «create»
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
};

export default memo(MessageEdge);