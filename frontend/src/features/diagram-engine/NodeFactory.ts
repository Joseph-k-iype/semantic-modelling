// frontend/src/features/diagram-engine/NodeFactory.ts

import { ComponentType } from 'react';
import { NodeTypes, EdgeTypes, EdgeProps, NodeProps } from 'reactflow';

// Import node components (all use default exports)
import EntityNode from '../../components/nodes/er/EntityNode/EntityNode';
import ClassNode from '../../components/nodes/uml/ClassNode/ClassNode';
import TaskNode from '../../components/nodes/bpmn/TaskNode/TaskNode';
import EventNode from '../../components/nodes/bpmn/EventNode/EventNode';
import GatewayNode from '../../components/nodes/bpmn/GatewayNode/GatewayNode';
import PoolNode from '../../components/nodes/bpmn/PoolNode/PoolNode';
import LifelineNode from '../../components/nodes/uml/LifelineNode/LifelineNode';

// Import edge components (all use default exports)
import RelationshipEdge from '../../components/edges/er/RelationshipEdge/RelationshipEdge';
import AssociationEdge from '../../components/edges/uml/AssociationEdge/AssociationEdge';
import MessageEdge from '../../components/edges/uml/MessageEdge/MessageEdge';
import SequenceFlowEdge from '../../components/edges/bpmn/SequenceFlowEdge/SequenceFlowEdge';

// Node type registry
export const nodeTypes: NodeTypes = {
  // ER Nodes
  ER_ENTITY: EntityNode as ComponentType<NodeProps>,
  ER_WEAK_ENTITY: EntityNode as ComponentType<NodeProps>,
  ER_ATTRIBUTE: EntityNode as ComponentType<NodeProps>,
  entityNode: EntityNode as ComponentType<NodeProps>,

  // UML Nodes
  UML_CLASS: ClassNode as ComponentType<NodeProps>,
  UML_INTERFACE: ClassNode as ComponentType<NodeProps>,
  UML_ABSTRACT_CLASS: ClassNode as ComponentType<NodeProps>,
  UML_PACKAGE: ClassNode as ComponentType<NodeProps>,
  UML_COMPONENT: ClassNode as ComponentType<NodeProps>,
  UML_NOTE: ClassNode as ComponentType<NodeProps>,
  classNode: ClassNode as ComponentType<NodeProps>,
  
  // UML Sequence Nodes
  UML_LIFELINE: LifelineNode as ComponentType<NodeProps>,
  lifelineNode: LifelineNode as ComponentType<NodeProps>,

  // BPMN Nodes
  BPMN_TASK: TaskNode as ComponentType<NodeProps>,
  BPMN_USER_TASK: TaskNode as ComponentType<NodeProps>,
  BPMN_SERVICE_TASK: TaskNode as ComponentType<NodeProps>,
  BPMN_MANUAL_TASK: TaskNode as ComponentType<NodeProps>,
  BPMN_SCRIPT_TASK: TaskNode as ComponentType<NodeProps>,
  taskNode: TaskNode as ComponentType<NodeProps>,
  
  BPMN_START_EVENT: EventNode as ComponentType<NodeProps>,
  BPMN_END_EVENT: EventNode as ComponentType<NodeProps>,
  BPMN_INTERMEDIATE_EVENT: EventNode as ComponentType<NodeProps>,
  eventNode: EventNode as ComponentType<NodeProps>,
  
  BPMN_GATEWAY_EXCLUSIVE: GatewayNode as ComponentType<NodeProps>,
  BPMN_GATEWAY_PARALLEL: GatewayNode as ComponentType<NodeProps>,
  BPMN_GATEWAY_INCLUSIVE: GatewayNode as ComponentType<NodeProps>,
  gatewayNode: GatewayNode as ComponentType<NodeProps>,
  
  BPMN_POOL: PoolNode as ComponentType<NodeProps>,
  BPMN_LANE: PoolNode as ComponentType<NodeProps>,
  poolNode: PoolNode as ComponentType<NodeProps>,
};

// Edge type registry with proper typing
export const edgeTypes: EdgeTypes = {
  // ER Edges
  ER_RELATIONSHIP: RelationshipEdge as ComponentType<EdgeProps>,
  ER_ATTRIBUTE_LINK: RelationshipEdge as ComponentType<EdgeProps>,
  relationshipEdge: RelationshipEdge as ComponentType<EdgeProps>,

  // UML Edges
  UML_ASSOCIATION: AssociationEdge as ComponentType<EdgeProps>,
  UML_AGGREGATION: AssociationEdge as ComponentType<EdgeProps>,
  UML_COMPOSITION: AssociationEdge as ComponentType<EdgeProps>,
  UML_GENERALIZATION: AssociationEdge as ComponentType<EdgeProps>,
  UML_DEPENDENCY: AssociationEdge as ComponentType<EdgeProps>,
  UML_REALIZATION: AssociationEdge as ComponentType<EdgeProps>,
  associationEdge: AssociationEdge as ComponentType<EdgeProps>,
  
  // UML Sequence Message Edge
  UML_MESSAGE: MessageEdge as ComponentType<EdgeProps>,
  messageEdge: MessageEdge as ComponentType<EdgeProps>,

  // BPMN Edges
  BPMN_SEQUENCE_FLOW: SequenceFlowEdge as ComponentType<EdgeProps>,
  BPMN_MESSAGE_FLOW: SequenceFlowEdge as ComponentType<EdgeProps>,
  BPMN_ASSOCIATION: SequenceFlowEdge as ComponentType<EdgeProps>,
  sequenceFlowEdge: SequenceFlowEdge as ComponentType<EdgeProps>,
};

// Factory function to create nodes
export function createNode(
  type: string,
  position: { x: number; y: number },
  data: any
) {
  return {
    id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    position,
    data,
  };
}

// Factory function to create edges
export function createEdge(
  source: string,
  target: string,
  type: string,
  data: any = {}
) {
  return {
    id: `edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    source,
    target,
    type,
    data,
  };
}

// Helper to get default node data based on type
export function getDefaultNodeData(type: string, _position?: { x: number; y: number }): any {
  if (type.startsWith('ER_') || type === 'entityNode') {
    return {
      label: 'Entity',
      attributes: [],
      primaryKeys: [],
      foreignKeys: []
    };
  }
  
  if (type.startsWith('UML_CLASS') || type === 'classNode') {
    return {
      label: 'Class',
      stereotype: '',
      attributes: [],
      methods: [],
      isAbstract: false
    };
  }
  
  if (type.startsWith('UML_LIFELINE') || type === 'lifelineNode') {
    return {
      label: 'Object',
      stereotype: '',
      lifelineHeight: 400
    };
  }
  
  if (type.startsWith('BPMN_TASK') || type === 'taskNode') {
    return {
      label: 'Task',
      taskType: 'task'
    };
  }
  
  if (type.startsWith('BPMN_') && type.includes('EVENT') || type === 'eventNode') {
    return {
      label: 'Event',
      eventType: 'start',
      eventTrigger: 'none'
    };
  }
  
  if (type.startsWith('BPMN_GATEWAY') || type === 'gatewayNode') {
    return {
      label: 'Gateway',
      gatewayType: 'exclusive'
    };
  }
  
  if (type.startsWith('BPMN_POOL') || type.startsWith('BPMN_LANE') || type === 'poolNode') {
    return {
      label: 'Pool',
      poolType: 'pool',
      width: 400,
      height: 200
    };
  }
  
  return {
    label: 'Node'
  };
}

// Helper to get default edge data based on type
export function getDefaultEdgeData(type: string): any {
  if (type.startsWith('ER_') || type === 'relationshipEdge') {
    return {
      label: '',
      sourceCardinality: '1',
      targetCardinality: 'N',
      isIdentifying: false
    };
  }
  
  if (type.startsWith('UML_ASSOCIATION') || type === 'associationEdge') {
    return {
      label: '',
      associationType: 'association',
      sourceMultiplicity: '1',
      targetMultiplicity: '1'
    };
  }
  
  if (type.startsWith('UML_MESSAGE') || type === 'messageEdge') {
    return {
      label: 'message()',
      messageType: 'sync',
      sequence: 1
    };
  }
  
  if (type.startsWith('BPMN_') || type === 'sequenceFlowEdge') {
    return {
      label: '',
      condition: '',
      isDefault: false
    };
  }
  
  return {
    label: ''
  };
}

export default {
  nodeTypes,
  edgeTypes,
  createNode,
  createEdge,
  getDefaultNodeData,
  getDefaultEdgeData,
};