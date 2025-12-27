// frontend/src/components/nodes/bpmn/EventNode/EventNode.tsx
import { memo, useState } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { Play, Square, Circle, Clock, Mail, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

export const EventNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const event = data.event;

  if (!event) {
    return (
      <div className="w-10 h-10 rounded-full border-2 border-gray-400 bg-white flex items-center justify-center">
        <Circle className="w-5 h-5 text-gray-400" />
      </div>
    );
  }

  // Get event icon based on definition
  const getEventIcon = () => {
    switch (event.eventDefinition) {
      case 'message':
        return <Mail className="w-4 h-4" />;
      case 'timer':
        return <Clock className="w-4 h-4" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4" />;
      case 'signal':
        return <Circle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  // Determine border style based on event type
  const getBorderStyle = () => {
    switch (event.eventType) {
      case 'start':
        return 'border-2 border-green-600';
      case 'end':
        return 'border-4 border-red-600';
      case 'intermediate':
        return 'border-2 border-orange-600 border-double';
      default:
        return 'border-2 border-gray-400';
    }
  };

  // Determine background color
  const getBackgroundColor = () => {
    switch (event.eventType) {
      case 'start':
        return 'bg-green-50';
      case 'end':
        return 'bg-red-50';
      case 'intermediate':
        return 'bg-orange-50';
      default:
        return 'bg-white';
    }
  };

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2 rounded-full'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {event.eventType !== 'start' && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}

      <div className="flex flex-col items-center">
        {/* Event Circle */}
        <div
          className={clsx(
            'w-12 h-12 rounded-full flex items-center justify-center transition-all',
            getBorderStyle(),
            getBackgroundColor(),
            isHovered && 'shadow-md scale-110'
          )}
        >
          {getEventIcon()}
        </div>

        {/* Event Label */}
        {event.name && (
          <div className="mt-2 text-xs text-gray-600 text-center max-w-[100px] break-words">
            {event.name}
          </div>
        )}
      </div>

      {event.eventType !== 'end' && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}
    </div>
  );
});

EventNode.displayName = 'EventNode';