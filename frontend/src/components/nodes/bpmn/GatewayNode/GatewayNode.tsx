// frontend/src/components/nodes/bpmn/GatewayNode/GatewayNode.tsx
import { memo, useState } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { X, Plus, Circle, Diamond } from 'lucide-react';
import clsx from 'clsx';

export const GatewayNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const gateway = data.gateway;

  if (!gateway) {
    return (
      <div className="w-12 h-12 bg-yellow-100 border-2 border-yellow-600 rotate-45 flex items-center justify-center">
        <Diamond className="w-5 h-5 text-yellow-600 -rotate-45" />
      </div>
    );
  }

  // Get gateway symbol based on type
  const getGatewaySymbol = () => {
    switch (gateway.gatewayType) {
      case 'exclusive':
        return <X className="w-6 h-6 text-yellow-700 font-bold stroke-[3]" />;
      case 'parallel':
        return <Plus className="w-6 h-6 text-blue-700 font-bold stroke-[3]" />;
      case 'inclusive':
        return <Circle className="w-6 h-6 text-purple-700 font-bold stroke-[3]" />;
      case 'eventBased':
        return (
          <div className="relative">
            <Circle className="w-6 h-6 text-orange-700 stroke-[2]" />
            <Circle className="w-4 h-4 text-orange-700 stroke-[2] absolute top-1 left-1" />
          </div>
        );
      default:
        return <X className="w-6 h-6 text-gray-700" />;
    }
  };

  // Get gateway color based on type
  const getGatewayColor = () => {
    switch (gateway.gatewayType) {
      case 'exclusive':
        return 'bg-yellow-100 border-yellow-600';
      case 'parallel':
        return 'bg-blue-100 border-blue-600';
      case 'inclusive':
        return 'bg-purple-100 border-purple-600';
      case 'eventBased':
        return 'bg-orange-100 border-orange-600';
      default:
        return 'bg-gray-100 border-gray-600';
    }
  };

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-gray-400 border-2 border-white"
      />

      <div className="flex flex-col items-center">
        {/* Gateway Diamond */}
        <div
          className={clsx(
            'w-14 h-14 border-2 rotate-45 flex items-center justify-center transition-all',
            getGatewayColor(),
            isHovered && 'shadow-md scale-110'
          )}
        >
          <div className="-rotate-45">
            {getGatewaySymbol()}
          </div>
        </div>

        {/* Gateway Label */}
        {gateway.name && (
          <div className="mt-2 text-xs text-gray-600 text-center max-w-[100px] break-words">
            {gateway.name}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-gray-400 border-2 border-white"
      />
    </div>
  );
});

GatewayNode.displayName = 'GatewayNode';