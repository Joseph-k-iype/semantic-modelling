// frontend/src/components/edges/er/RelationshipEdge/RelationshipEdge.tsx
// ENHANCED VERSION - Keeps ALL existing features + adds cardinality selectors
import { memo, useState, useCallback } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { Edit2, Check, X } from 'lucide-react';
import clsx from 'clsx';

export interface ERRelationshipData {
  label?: string;
  sourceCardinality?: string;
  targetCardinality?: string;
  isIdentifying?: boolean;
  color?: string;
  strokeWidth?: number;
}

export const RelationshipEdge = memo<EdgeProps<ERRelationshipData>>(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  markerEnd
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
    // Update would be handled by parent component / store
    setIsEditingLabel(false);
    // TODO: Emit update event
  }, []);

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
    // TODO: Emit update event
  }, []);

  const handleTargetCardinalityChange = useCallback((value: string) => {
    setTargetCard(value);
    // TODO: Emit update event
  }, []);

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
        }}
      />

      <EdgeLabelRenderer>
        {/* Source Cardinality Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${sourceCardX}px, ${sourceCardY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <select
            value={sourceCard}
            onChange={(e) => handleSourceCardinalityChange(e.target.value)}
            className={clsx(
              'px-2 py-1 text-xs font-bold bg-white border rounded shadow-sm',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              'cursor-pointer'
            )}
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
          }}
          className="nodrag nopan"
        >
          {isEditingLabel ? (
            <div className="flex items-center gap-1 bg-white border border-blue-300 rounded shadow-md p-1">
              <input
                type="text"
                value={tempLabel}
                onChange={(e) => setTempLabel(e.target.value)}
                onKeyDown={handleLabelKeyDown}
                autoFocus
                className="px-2 py-1 text-xs border-none focus:outline-none w-32"
                placeholder="relationship"
              />
              <button
                onClick={handleSaveLabel}
                className="p-1 text-green-600 hover:bg-green-100 rounded"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={handleCancelEditLabel}
                className="p-1 text-red-600 hover:bg-red-100 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div
              onClick={handleStartEditLabel}
              className={clsx(
                'px-2 py-1 text-xs font-medium bg-white border rounded shadow-sm cursor-text',
                'hover:border-blue-300 transition-colors',
                selected && 'border-blue-500'
              )}
            >
              {data?.label || 'relationship'}
              <button className="ml-1 opacity-0 hover:opacity-100">
                <Edit2 className="w-3 h-3 inline" />
              </button>
            </div>
          )}
        </div>

        {/* Target Cardinality Selector */}
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${targetCardX}px, ${targetCardY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <select
            value={targetCard}
            onChange={(e) => handleTargetCardinalityChange(e.target.value)}
            className={clsx(
              'px-2 py-1 text-xs font-bold bg-white border rounded shadow-sm',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              'cursor-pointer'
            )}
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