// frontend/src/components/edges/uml/AssociationEdge/AssociationEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

export type AssociationType = 'association' | 'generalization' | 'dependency' | 'aggregation' | 'composition';
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

const AssociationEdge: React.FC<EdgeProps<AssociationEdgeData>> = ({
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

  const edgeColor = data?.color || '#000000';
  const strokeWidth = data?.strokeWidth || 2;
  const associationType = data?.associationType || 'association';

  // Calculate positions for multiplicity labels
  const sourceMultX = sourceX + (labelX - sourceX) * 0.15;
  const sourceMultY = sourceY + (labelY - sourceY) * 0.15;
  const targetMultX = targetX + (labelX - targetX) * 0.15;
  const targetMultY = targetY + (labelY - targetY) * 0.15;

  // Get stroke style based on association type
  const getStrokeStyle = () => {
    if (associationType === 'dependency') {
      return '5,5'; // dashed
    }
    return undefined;
  };

  // Get marker end based on association type
  const getMarkerEnd = () => {
    const angle = Math.atan2(targetY - sourceY, targetX - sourceX);
    const arrowSize = 12;
    
    switch (associationType) {
      case 'generalization':
        // Hollow triangle (inheritance)
        return (
          <marker
            id={`generalization-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
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
      case 'composition':
        // Filled diamond
        return (
          <marker
            id={`composition-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polygon
              points={`0,${arrowSize / 2} ${arrowSize / 2},0 ${arrowSize},${arrowSize / 2} ${arrowSize / 2},${arrowSize}`}
              fill={edgeColor}
            />
          </marker>
        );
      case 'aggregation':
        // Hollow diamond
        return (
          <marker
            id={`aggregation-${id}`}
            markerWidth={arrowSize}
            markerHeight={arrowSize}
            refX={arrowSize / 2}
            refY={arrowSize / 2}
            orient="auto"
          >
            <polygon
              points={`0,${arrowSize / 2} ${arrowSize / 2},0 ${arrowSize},${arrowSize / 2} ${arrowSize / 2},${arrowSize}`}
              fill="white"
              stroke={edgeColor}
              strokeWidth={strokeWidth}
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
              placeholder="association name"
              style={{
                padding: '2px 6px',
                fontSize: '11px',
                background: 'white',
                border: '1px solid #ccc',
                borderRadius: '3px',
                minWidth: '80px',
                fontStyle: 'italic'
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
                  fontStyle: 'italic'
                }}
              >
                {label}
              </div>
            )
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
};

export default memo(AssociationEdge);