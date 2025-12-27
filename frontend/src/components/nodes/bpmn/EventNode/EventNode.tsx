import React, { memo } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { Play, Square, Clock, Mail, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

export const EventNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const event = data.event;

  if (!event) {
    return (
      <BaseNode id={id} data={data} selected={selected} showHandles={false}>
        <div className="w-12 h-12 rounded-full bg-gray-300" />
      </BaseNode>
    );
  }

  const getEventIcon = () => {
    switch (event.eventDefinition) {
      case 'message':
        return <Mail className="w-5 h-5" />;
      case 'timer':
        return <Clock className="w-5 h-5" />;
      case 'error':
        return <AlertCircle className="w-5 h-5" />;
      default:
        if (event.eventType === 'start') return <Play className="w-5 h-5" />;
        if (event.eventType === 'end') return <Square className="w-5 h-5" />;
        return null;
    }
  };

  const getBorderStyle = () => {
    if (event.eventType === 'start') return 'border-4 border-green-500';
    if (event.eventType === 'end') return 'border-4 border-red-500';
    return 'border-2 border-orange-500';
  };

  const getBackgroundColor = () => {
    if (event.eventType === 'start') return 'bg-green-50';
    if (event.eventType === 'end') return 'bg-red-50';
    return 'bg-orange-50';
  };

  return (
    <BaseNode 
      id={id} 
      data={data} 
      selected={selected}
      className="!border-0 !shadow-none !bg-transparent"
      showHandles={false}
    >
      <div className="relative">
        <div className={clsx(
          'w-16 h-16 rounded-full flex items-center justify-center',
          getBorderStyle(),
          getBackgroundColor()
        )}>
          <div className={clsx(
            event.eventType === 'start' && 'text-green-600',
            event.eventType === 'end' && 'text-red-600',
            event.eventType === 'intermediate' && 'text-orange-600'
          )}>
            {getEventIcon()}
          </div>
        </div>
        
        {event.name && (
          <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap text-xs text-gray-600 bg-white px-2 py-1 rounded shadow-sm">
            {event.name}
          </div>
        )}
      </div>
    </BaseNode>
  );
});

EventNode.displayName = 'EventNode';