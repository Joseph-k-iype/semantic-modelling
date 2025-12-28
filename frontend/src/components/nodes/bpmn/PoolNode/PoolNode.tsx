// frontend/src/components/nodes/bpmn/PoolNode/PoolNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { NodeProps } from 'reactflow';

export interface Lane {
  id: string;
  name: string;
  height: number;
}

export interface PoolNodeData {
  label: string;
  lanes: Lane[];
  isHorizontal?: boolean;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const PoolNode: React.FC<NodeProps<PoolNodeData>> = ({ data, selected, id }) => {
  const [isEditingPool, setIsEditingPool] = useState(false);
  const [poolName, setPoolName] = useState(data.label);
  const [lanes, setLanes] = useState<Lane[]>(data.lanes || [
    { id: 'lane-1', name: 'Lane 1', height: 150 }
  ]);
  const [editingLaneId, setEditingLaneId] = useState<string | null>(null);

  const handlePoolNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setPoolName(e.target.value);
  }, []);

  const handlePoolNameBlur = useCallback(() => {
    setIsEditingPool(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: poolName, lanes });
    }
  }, [id, poolName, lanes]);

  const handleLaneNameChange = useCallback((laneId: string, newName: string) => {
    setLanes(prev => prev.map(lane => 
      lane.id === laneId ? { ...lane, name: newName } : lane
    ));
  }, []);

  const handleLaneNameBlur = useCallback(() => {
    setEditingLaneId(null);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: poolName, lanes });
    }
  }, [id, poolName, lanes]);

  const addLane = useCallback(() => {
    const newLane: Lane = {
      id: `lane-${Date.now()}`,
      name: `Lane ${lanes.length + 1}`,
      height: 150
    };
    setLanes(prev => [...prev, newLane]);
  }, [lanes.length]);

  const backgroundColor = data.color || '#f0f0f0';
  const textColor = data.textColor || '#000000';
  const isHorizontal = data.isHorizontal !== false;

  const totalHeight = lanes.reduce((sum, lane) => sum + lane.height, 0);
  const poolWidth = 800;
  const headerWidth = 40;

  return (
    <div 
      className="pool-node"
      style={{
        border: `2px solid ${textColor}`,
        borderRadius: '4px',
        boxShadow: selected ? '0 0 0 2px #3b82f6' : '0 2px 4px rgba(0,0,0,0.1)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: isHorizontal ? 'row' : 'column',
        zIndex: data.zIndex || 1
      }}
    >
      {/* Pool Header */}
      <div
        style={{
          width: isHorizontal ? `${headerWidth}px` : `${poolWidth}px`,
          height: isHorizontal ? `${totalHeight}px` : `${headerWidth}px`,
          backgroundColor: `${backgroundColor}dd`,
          borderRight: isHorizontal ? `1px solid ${textColor}` : 'none',
          borderBottom: !isHorizontal ? `1px solid ${textColor}` : 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          writingMode: isHorizontal ? 'vertical-rl' : 'horizontal-tb',
          transform: isHorizontal ? 'rotate(180deg)' : 'none',
          fontWeight: 'bold',
          fontSize: '14px',
          color: textColor,
          cursor: 'text',
          padding: '8px'
        }}
        onDoubleClick={() => setIsEditingPool(true)}
      >
        {isEditingPool ? (
          <input
            type="text"
            value={poolName}
            onChange={handlePoolNameChange}
            onBlur={handlePoolNameBlur}
            autoFocus
            style={{
              border: 'none',
              background: 'transparent',
              color: textColor,
              fontWeight: 'bold',
              textAlign: 'center',
              outline: 'none',
              width: '100%'
            }}
          />
        ) : (
          poolName
        )}
      </div>

      {/* Lanes Container */}
      <div 
        style={{
          display: 'flex',
          flexDirection: isHorizontal ? 'column' : 'row',
          flex: 1
        }}
      >
        {lanes.map((lane, index) => (
          <div
            key={lane.id}
            style={{
              width: isHorizontal ? `${poolWidth - headerWidth}px` : 'auto',
              height: isHorizontal ? `${lane.height}px` : `${totalHeight}px`,
              borderBottom: isHorizontal && index < lanes.length - 1 ? `1px solid ${textColor}` : 'none',
              borderRight: !isHorizontal && index < lanes.length - 1 ? `1px solid ${textColor}` : 'none',
              backgroundColor: index % 2 === 0 ? backgroundColor : `${backgroundColor}cc`,
              display: 'flex',
              position: 'relative',
              minWidth: isHorizontal ? 'auto' : '200px',
              flex: !isHorizontal ? 1 : 'none'
            }}
          >
            {/* Lane Header */}
            <div
              style={{
                width: isHorizontal ? '30px' : '100%',
                height: isHorizontal ? '100%' : '30px',
                borderRight: isHorizontal ? `1px solid ${textColor}33` : 'none',
                borderBottom: !isHorizontal ? `1px solid ${textColor}33` : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                writingMode: isHorizontal ? 'vertical-rl' : 'horizontal-tb',
                transform: isHorizontal ? 'rotate(180deg)' : 'none',
                fontSize: '12px',
                color: textColor,
                cursor: 'text',
                padding: '4px',
                fontWeight: '500'
              }}
              onDoubleClick={() => setEditingLaneId(lane.id)}
            >
              {editingLaneId === lane.id ? (
                <input
                  type="text"
                  value={lane.name}
                  onChange={(e) => handleLaneNameChange(lane.id, e.target.value)}
                  onBlur={handleLaneNameBlur}
                  autoFocus
                  style={{
                    border: 'none',
                    background: 'transparent',
                    color: textColor,
                    fontSize: '12px',
                    textAlign: 'center',
                    outline: 'none',
                    width: '100%'
                  }}
                />
              ) : (
                lane.name
              )}
            </div>

            {/* Lane Content Area */}
            <div 
              style={{
                flex: 1,
                padding: '8px',
                position: 'relative'
              }}
            >
              {/* Content goes here - tasks, events, etc. */}
            </div>
          </div>
        ))}
      </div>

      {/* Add Lane Button */}
      <button
        onClick={addLane}
        style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          padding: '4px 8px',
          background: 'white',
          border: `1px solid ${textColor}`,
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '11px',
          color: textColor,
          opacity: 0.7
        }}
      >
        + Add Lane
      </button>
    </div>
  );
};

export default memo(PoolNode);