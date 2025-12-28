// frontend/src/components/edges/bpmn/SequenceFlowEdge/SequenceFlowEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export interface SequenceFlowEdgeData {
  label?: string;
  condition?: string;
  isDefault?: boolean;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const SequenceFlowEdge: React.FC<EdgeProps<SequenceFlowEdgeData>> = memo(({
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
  const [isEditingCondition, setIsEditingCondition] = useState(false);
  const [condition, setCondition] = useState(data?.condition || '');

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

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
        condition: data?.condition,
        isDefault: data?.isDefault
      });
    }
  }, [id, label, data?.condition, data?.isDefault]);

  const handleConditionChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setCondition(e.target.value);
  }, []);

  const handleConditionBlur = useCallback(() => {
    setIsEditingCondition(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label: data?.label,
        condition, 
        isDefault: data?.isDefault
      });
    }
  }, [id, condition, data?.label, data?.isDefault]);

  const getMarkerEnd = () => {
    const arrowSize = 10;
    
    if (data?.isDefault) {
      // Default flow has a diagonal slash marker at source
      return (
        <>
          <marker
            id={`default-flow-${id}`}
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
        </>
      );
    }
    
    return (
      <marker
        id={`sequence-flow-${id}`}
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
  };

  return (
    <>
      <defs>
        {getMarkerEnd()}
      </defs>
      
      {/* Default flow marker at source */}
      {data?.isDefault && (
        <path
          d={`M ${sourceX - 10} ${sourceY - 5} L ${sourceX - 5} ${sourceY + 5}`}
          stroke={edgeColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
      )}
      
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={`url(#${data?.isDefault ? 'default' : 'sequence'}-flow-${id})`}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Flow Label */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 20}px)`,
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
          ) : label ? (
            <div
              style={{
                padding: '2px 6px',
                background: 'white',
                border: `1px solid ${selected ? '#3b82f6' : '#d1d5db'}`,
                borderRadius: '3px',
                fontSize: '11px',
                cursor: 'text',
                minWidth: '40px',
                textAlign: 'center'
              }}
            >
              {label}
            </div>
          ) : null}
        </div>

        {/* Condition Label */}
        {(condition || isEditingCondition) && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + 5}px)`,
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
                placeholder="[condition]"
                autoFocus
                style={{
                  padding: '2px 6px',
                  fontSize: '10px',
                  border: '1px solid #3b82f6',
                  borderRadius: '3px',
                  outline: 'none',
                  minWidth: '80px',
                  background: 'white',
                  fontFamily: 'monospace'
                }}
              />
            ) : (
              <div
                style={{
                  padding: '2px 6px',
                  background: '#fef3c7',
                  border: '1px solid #f59e0b',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: 'text',
                  fontFamily: 'monospace',
                  fontStyle: 'italic'
                }}
              >
                [{condition}]
              </div>
            )}
          </div>
        )}

        {/* Default Flow Indicator */}
        {data?.isDefault && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + 30}px)`,
              pointerEvents: 'none',
              zIndex: data?.zIndex || 1
            }}
          >
            <div
              style={{
                padding: '2px 6px',
                background: '#dbeafe',
                border: '1px solid #3b82f6',
                borderRadius: '3px',
                fontSize: '9px',
                fontWeight: 'bold',
                color: '#1e40af'
              }}
            >
              default
            </div>
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
});

SequenceFlowEdge.displayName = 'SequenceFlowEdge';

export default SequenceFlowEdge;