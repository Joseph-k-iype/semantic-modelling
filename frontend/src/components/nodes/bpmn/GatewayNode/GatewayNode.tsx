import { memo } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { BPMNNodeData } from '../../../../types/diagram.types';
import clsx from 'clsx';

export const GatewayNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const gateway = data.gateway;

  if (!gateway) {
    return (
      <BaseNode id={id} data={data} selected={selected} showHandles={false}>
        <div className="w-12 h-12 bg-yellow-300 transform rotate-45" />
      </BaseNode>
    );
  }

  const getGatewaySymbol = () => {
    switch (gateway.gatewayType) {
      case 'exclusive':
        return (
          <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M6 6 L18 18 M18 6 L6 18" strokeWidth="2" strokeLinecap="round" />
          </svg>
        );
      case 'parallel':
        return (
          <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 6 L12 18 M6 12 L18 12" strokeWidth="2" strokeLinecap="round" />
          </svg>
        );
      case 'inclusive':
        return (
          <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="6" strokeWidth="2" />
          </svg>
        );
      case 'eventBased':
        return (
          <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="6" strokeWidth="2" />
            <circle cx="12" cy="12" r="3" strokeWidth="2" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getGatewayColor = () => {
    switch (gateway.gatewayType) {
      case 'exclusive':
        return 'text-yellow-600';
      case 'parallel':
        return 'text-blue-600';
      case 'inclusive':
        return 'text-green-600';
      case 'eventBased':
        return 'text-purple-600';
      default:
        return 'text-gray-600';
    }
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
          'w-14 h-14 bg-yellow-100 border-4 border-yellow-500 transform rotate-45 flex items-center justify-center',
          selected && 'border-blue-500'
        )}>
          <div className={clsx('transform -rotate-45', getGatewayColor())}>
            {getGatewaySymbol()}
          </div>
        </div>
        
        {gateway.name && (
          <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap text-xs text-gray-600 bg-white px-2 py-1 rounded shadow-sm">
            {gateway.name}
          </div>
        )}
      </div>
    </BaseNode>
  );
});

GatewayNode.displayName = 'GatewayNode';