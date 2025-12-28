// frontend/src/components/edges/bpmn/SequenceFlowEdge/SequenceFlowEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export type FlowType = 'sequence' | 'message' | 'association';
export type SequenceFlowType = 'normal' | 'conditional' | 'default';

export interface SequenceFlowEdgeData {
  label?: string;
  flowType: FlowType;
  sequenceFlowType?: SequenceFlowType;
  condition?: string;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const SequenceFlowEdge: React.FC<EdgeProps<SequenceFlowEdgeData>> = ({
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
  const [isEditingCondition, setIsEditingCondition] = useState(false);
  const [label, setLabel] = useState(data?.label || '');
  const [condition, setCondition] = useState(data?.condition || '');
  const [flowType, setFlowType] = useState<FlowType>(data?.flowType || 'sequence');
  const [sequenceFlowType, setSequenceFlowType] = useState<SequenceFlowType>(data?.sequenceFlowType || 'normal');

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, condition, flowType, sequenceFlowType });
    }
  }, [id, label, condition, flowType, sequenceFlowType]);

  const handleConditionChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setCondition(e.target.value);
  }, []);

  const handleConditionBlur = useCallback(() => {
    setIsEditingCondition(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, condition, flowType, sequenceFlowType });
    }
  }, [id, label, condition, flowType, sequenceFlowType]);

  const handleFlowTypeChange = useCallback((type: FlowType) => {
    setFlowType(type);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, condition, flowType: type, sequenceFlowType });
    }
  }, [id, label, condition, sequenceFlowType]);

  const handleSequenceFlowTypeChange = useCallback((type: SequenceFlowType) => {
    setSequenceFlowType(type);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { label, condition, flowType, sequenceFlowType: type });
    }
  }, [id, label, condition, flowType]);

  const edgeColor = data?.color || '#000000';
  const strokeWidth = data?.strokeWidth || 2;

  // Get stroke style based on flow type
  const getStrokeStyle = () => {
    if (flowType === 'message') {
      return '8,4'; // dashed for message flow
    } else if (flowType === 'association') {
      return '2,2'; // dotted for association
    }
    return undefined; // solid for sequence flow
  };

  // Get marker start for default flow (slash mark)
  const getMarkerStart = () => {
    if (sequenceFlowType === 'default') {
      return (
        <marker
          id={`default-start-${id}`}
          markerWidth={12}
          markerHeight={12}
          refX={6}
          refY={6}
          orient="auto"
        >
          <line x1="3" y1="3" x2="9" y2="9" stroke={edgeColor} strokeWidth={strokeWidth} />
        </marker>
      );
    }
    return null;
  };

  // Get marker end based on flow type
  const getMarkerEnd = () => {
    const arrowSize = 10;
    
    if (flowType === 'message') {
      // Open arrow for message flow
      return (
        <marker
          id={`message-${id}`}
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
    } else if (flowType === 'association') {
      // No arrow for association
      return null;
    } else {
      // Filled arrow for sequence flow
      return (
        <marker
          id={`sequence-${id}`}
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
    }
  };

  // Calculate position for condition label (for conditional flows)
  const conditionX = sourceX + (labelX - sourceX) * 0.3;
  const conditionY = sourceY + (labelY - sourceY) * 0.3;

  return (
    <>
      <defs>
        {getMarkerStart()}
        {getMarkerEnd()}
      </defs>
      
      <BaseEdge
        id={id}
        path={edgePath}
        markerStart={sequenceFlowType === 'default' ? `url(#default-start-${id})` : undefined}
        markerEnd={flowType !== 'association' ? `url(#${flowType}-${id})` : undefined}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          strokeDasharray: getStrokeStyle(),
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Flow Type Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 35}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={flowType}
            onChange={(e) => handleFlowTypeChange(e.target.value as FlowType)}
            style={{
              padding: '2px 4px',
              fontSize: '10px',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              cursor: 'pointer',
              marginRight: '4px'
            }}
          >
            <option value="sequence">Sequence Flow</option>
            <option value="message">Message Flow</option>
            <option value="association">Association</option>
          </select>

          {flowType === 'sequence' && (
            <select
              value={sequenceFlowType}
              onChange={(e) => handleSequenceFlowTypeChange(e.target.value as SequenceFlowType)}
              style={{
                padding: '2px 4px',
                fontSize: '10px',
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              <option value="normal">Normal</option>
              <option value="conditional">Conditional</option>
              <option value="default">Default</option>
            </select>
          )}
        </div>

        {/* Conditional Flow - Condition Diamond and Text */}
        {sequenceFlowType === 'conditional' && (
          <>
            {/* Diamond shape */}
            <div
              style={{
                position: 'absolute',
                transform: `translate(-50%, -50%) translate(${conditionX}px, ${conditionY}px)`,
                width: '16px',
                height: '16px',
                backgroundColor: 'white',
                border: `1px solid ${edgeColor}`,
                transform: 'translate(-50%, -50%) rotate(45deg)',
                zIndex: data?.zIndex || 1
              }}
            />
            
            {/* Condition text */}
            <div
              style={{
                position: 'absolute',
                transform: `translate(-50%, -50%) translate(${conditionX}px, ${conditionY - 20}px)`,
                pointerEvents: 'all',
                zIndex: data?.zIndex || 1
              }}
              className="nodrag nopan"
              onDoubleClick={() => setIsEditingCondition(true)}
            >
              {isEditingCondition ? (
                <input
                  type="text"
                  value={condition}
                  onChange={handleConditionChange}
                  onBlur={handleConditionBlur}
                  autoFocus
                  placeholder="[condition]"
                  style={{
                    padding: '2px 6px',
                    fontSize: '10px',
                    background: 'white',
                    border: '1px solid #ccc',
                    borderRadius: '3px',
                    minWidth: '60px',
                    fontFamily: 'monospace'
                  }}
                />
              ) : (
                condition && (
                  <div
                    style={{
                      padding: '2px 6px',
                      fontSize: '10px',
                      background: 'white',
                      border: '1px solid #ccc',
                      borderRadius: '3px',
                      cursor: 'text',
                      fontFamily: 'monospace'
                    }}
                  >
                    [{condition}]
                  </div>
                )
              )}
            </div>
          </>
        )}

        {/* Flow Label */}
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
              placeholder="label"
              style={{
                padding: '2px 6px',
                fontSize: '11px',
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '3px',
                minWidth: '60px'
              }}
            />
          ) : (
            label && (
              <div
                style={{
                  padding: '2px 6px',
                  fontSize: '11px',
                  background: 'white',
                  border: '1px solid #ccc',
                  borderRadius: '3px',
                  cursor: 'text',
                  textAlign: 'center'
                }}
              >
                {label}
              </div>
            )
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
};

export default memo(SequenceFlowEdge);