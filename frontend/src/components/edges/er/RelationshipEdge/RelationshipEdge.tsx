// frontend/src/components/edges/er/RelationshipEdge/RelationshipEdge.tsx

import React, { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { Edit2, Check, X } from 'lucide-react';

export interface ERRelationshipData {
  label?: string;
  sourceCardinality?: string;
  targetCardinality?: string;
  isIdentifying?: boolean;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

const RelationshipEdge: React.FC<EdgeProps<ERRelationshipData>> = memo(({
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
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [tempLabel, setTempLabel] = useState(data?.label || '');
  const [sourceCard, setSourceCard] = useState(data?.sourceCardinality || '1');
  const [targetCard, setTargetCard] = useState(data?.targetCardinality || 'N');

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const handleStartEditLabel = useCallback(() => {
    setTempLabel(data?.label || '');
    setIsEditingLabel(true);
  }, [data?.label]);

  const handleSaveLabel = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label: tempLabel,
        sourceCardinality: sourceCard,
        targetCardinality: targetCard
      });
    }
  }, [id, tempLabel, sourceCard, targetCard]);

  const handleCancelEditLabel = useCallback(() => {
    setIsEditingLabel(false);
    setTempLabel(data?.label || '');
  }, [data?.label]);

  const handleLabelKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveLabel();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditLabel();
    }
  }, [handleSaveLabel, handleCancelEditLabel]);

  const handleSourceCardinalityChange = useCallback((value: string) => {
    setSourceCard(value);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label: tempLabel,
        sourceCardinality: value,
        targetCardinality: targetCard
      });
    }
  }, [id, tempLabel, targetCard]);

  const handleTargetCardinalityChange = useCallback((value: string) => {
    setTargetCard(value);
    if (window.updateEdgeData) {
      window.updateEdgeData(id, { 
        label: tempLabel,
        sourceCardinality: sourceCard,
        targetCardinality: value
      });
    }
  }, [id, tempLabel, sourceCard]);

  const edgeColor = data?.color || (selected ? '#3b82f6' : '#6b7280');
  const strokeWidth = data?.strokeWidth || (selected ? 3 : 2);

  // Calculate positions for cardinality labels
  const sourceCardX = sourceX + (labelX - sourceX) * 0.2;
  const sourceCardY = sourceY + (labelY - sourceY) * 0.2;
  const targetCardX = targetX + (labelX - targetX) * 0.2;
  const targetCardY = targetY + (labelY - targetY) * 0.2;

  return (
    <>
      <defs>
        <marker
          id={`relationship-${id}`}
          markerWidth="20"
          markerHeight="20"
          refX="10"
          refY="10"
          orient="auto"
        >
          <path
            d="M 0 5 L 10 10 L 0 15 Z"
            fill={edgeColor}
          />
        </marker>
      </defs>

      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={`url(#relationship-${id})`}
        style={{
          stroke: edgeColor,
          strokeWidth: strokeWidth,
          strokeDasharray: data?.isIdentifying ? undefined : '5,5',
          zIndex: data?.zIndex || 1
        }}
      />

      <EdgeLabelRenderer>
        {/* Source Cardinality Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${sourceCardX}px, ${sourceCardY}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={sourceCard}
            onChange={(e) => handleSourceCardinalityChange(e.target.value)}
            style={{
              padding: '2px 6px',
              fontSize: '11px',
              fontWeight: 'bold',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <option value="1">1</option>
            <option value="N">N</option>
            <option value="0..1">0..1</option>
            <option value="1..N">1..N</option>
            <option value="0..N">0..N</option>
            <option value="M">M</option>
          </select>
        </div>

        {/* Relationship Label */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          {isEditingLabel ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <input
                type="text"
                value={tempLabel}
                onChange={(e) => setTempLabel(e.target.value)}
                onKeyDown={handleLabelKeyDown}
                autoFocus
                style={{
                  padding: '4px 8px',
                  fontSize: '12px',
                  border: '2px solid #3b82f6',
                  borderRadius: '4px',
                  outline: 'none',
                  minWidth: '80px'
                }}
              />
              <button
                onClick={handleSaveLabel}
                style={{
                  padding: '4px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <Check size={14} />
              </button>
              <button
                onClick={handleCancelEditLabel}
                style={{
                  padding: '4px',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <div
              style={{
                padding: '4px 8px',
                background: 'white',
                border: `2px solid ${selected ? '#3b82f6' : '#d1d5db'}`,
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: '500',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                minWidth: '60px',
                justifyContent: 'center'
              }}
              onDoubleClick={handleStartEditLabel}
            >
              <span>{data?.label || 'relates to'}</span>
              <Edit2 size={12} style={{ opacity: 0.5 }} />
            </div>
          )}
        </div>

        {/* Target Cardinality Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${targetCardX}px, ${targetCardY}px)`,
            pointerEvents: 'all',
            zIndex: data?.zIndex || 1
          }}
          className="nodrag nopan"
        >
          <select
            value={targetCard}
            onChange={(e) => handleTargetCardinalityChange(e.target.value)}
            style={{
              padding: '2px 6px',
              fontSize: '11px',
              fontWeight: 'bold',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '3px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <option value="1">1</option>
            <option value="N">N</option>
            <option value="0..1">0..1</option>
            <option value="1..N">1..N</option>
            <option value="0..N">0..N</option>
            <option value="M">M</option>
          </select>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

RelationshipEdge.displayName = 'RelationshipEdge';

export default RelationshipEdge;