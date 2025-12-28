// frontend/src/components/edges/uml/AssociationEdge/AssociationEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export type AssociationType = 'association' | 'generalization' | 'dependency' | 'aggregation' | 'composition' | 'realization';
export type Multiplicity = '1' | '0..1' | '1..*' | '0..*' | '*';

export interface AssociationEdgeData {
  label?: string;
  associationType: AssociationType;
  sourceMultiplicity?: Multiplicity;
  targetMultiplicity?: Multiplicity;
  sourceRole?: string;
  targetRole?: string;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const AssociationEdge: React.FC<EdgeProps<AssociationEdgeData>> = memo(({
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
  const [sourceMultiplicity, setSourceMultiplicity] = useState<Multiplicity>(data?.sourceMultiplicity || '1');
  const [targetMultiplicity, setTargetMultiplicity] = useState<Multiplicity>(data?.targetMultiplicity || '1');

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const associationType = data?.associationType || 'association';
  const edgeColor = data?.color || (selected ? '#3b82f6' : '#6b7280');
  const strokeWidth = data?.strokeWidth || 2;

  // Calculate positions for multiplicity labels
  const sourceMultX = sourceX + (labelX - sourceX) * 0.15;
  const sourceMultY = sourceY + (labelY - sourceY) * 0.15;
  const targetMultX = targetX + (labelX - targetX) * 0.15;
  const targetMultY = targetY + (labelY - targetY) * 0.15;

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label, 
        sourceMultiplicity, 
        targetMultiplicity,
        associationType: data?.associationType
      });
    }
  }, [id, label, sourceMultiplicity, targetMultiplicity, data?.associationType]);

  const handleMultiplicityChange = useCallback((type: 'source' | 'target', value: Multiplicity) => {
    if (type === 'source') {
      setSourceMultiplicity(value);
    } else {
      setTargetMultiplicity(value);
    }
    
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label,
        sourceMultiplicity: type === 'source' ? value : sourceMultiplicity,
        targetMultiplicity: type === 'target' ? value : targetMultiplicity,
        associationType: data?.associationType
      });
    }
  }, [id, label, sourceMultiplicity, targetMultiplicity, data?.associationType]);

  const getStrokeStyle = () => {
    switch (associationType) {
      case 'dependency':
        return '5,5';
      default:
        return undefined;
    }
  };

  const getMarkerEnd = () => {
    const arrowSize = 10;
    
    switch (associationType) {
      case 'generalization':
      case 'realization':
        // Filled triangle
        return (
          <marker
            id={`generalization-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polygon
              points={`0,0 ${arrowSize},${arrowSize / 2} 0,${arrowSize}`}
              fill="white"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      case 'aggregation':
        // Hollow diamond
        return (
          <marker
            id={`aggregation-${id}`}
            markerWidth={arrowSize * 1.5}
            markerHeight={arrowSize * 1.5}
            refX={arrowSize * 1.5}
            refY={arrowSize * 0.75}
            orient="auto"
          >
            <polygon
              points={`0,${arrowSize * 0.75} ${arrowSize * 0.75},0 ${arrowSize * 1.5},${arrowSize * 0.75} ${arrowSize * 0.75},${arrowSize * 1.5}`}
              fill="white"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
            />
          </marker>
        );
      case 'composition':
        // Filled diamond
        return (
          <marker
            id={`composition-${id}`}
            markerWidth={arrowSize * 1.5}
            markerHeight={arrowSize * 1.5}
            refX={arrowSize * 1.5}
            refY={arrowSize * 0.75}
            orient="auto"
          >
            <polygon
              points={`0,${arrowSize * 0.75} ${arrowSize * 0.75},0 ${arrowSize * 1.5},${arrowSize * 0.75} ${arrowSize * 0.75},${arrowSize * 1.5}`}
              fill={edgeColor}
            />
          </marker>
        );
      case 'dependency':
        // Open arrow
        return (
          <marker
            id={`dependency-${id}`}
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
      default:
        // Simple arrow for association
        return (
          <marker
            id={`association-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
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

  return (
    <>
      <defs>
        {getMarkerEnd()}
      </defs>
      
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={`url(#${associationType}-${id})`}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          strokeDasharray: getStrokeStyle(),
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Source Multiplicity */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${sourceMultX}px, ${sourceMultY}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={sourceMultiplicity}
            onChange={(e) => handleMultiplicityChange('source', e.target.value as Multiplicity)}
            style={{
              padding: '2px 4px',
              fontSize: '10px',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              cursor: 'pointer',
              fontFamily: 'monospace'
            }}
          >
            <option value="1">1</option>
            <option value="0..1">0..1</option>
            <option value="1..*">1..*</option>
            <option value="0..*">0..*</option>
            <option value="*">*</option>
          </select>
        </div>

        {/* Edge Label */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
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
                minWidth: '60px',
                background: 'white'
              }}
            />
          ) : (
            <div
              style={{
                padding: '2px 6px',
                background: 'white',
                border: `1px solid ${selected ? '#3b82f6' : '#d1d5db'}`,
                borderRadius: '3px',
                fontSize: '11px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                cursor: 'text',
                minWidth: '40px',
                textAlign: 'center'
              }}
            >
              {label || ''}
            </div>
          )}
        </div>

        {/* Target Multiplicity */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${targetMultX}px, ${targetMultY}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={targetMultiplicity}
            onChange={(e) => handleMultiplicityChange('target', e.target.value as Multiplicity)}
            style={{
              padding: '2px 4px',
              fontSize: '10px',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              cursor: 'pointer',
              fontFamily: 'monospace'
            }}
          >
            <option value="1">1</option>
            <option value="0..1">0..1</option>
            <option value="1..*">1..*</option>
            <option value="0..*">0..*</option>
            <option value="*">*</option>
          </select>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

AssociationEdge.displayName = 'AssociationEdge';

export default AssociationEdge;