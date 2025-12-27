import { ComponentType } from 'react';
import { NodeTypes, EdgeTypes, EdgeProps } from 'reactflow';

// Import node components
import { EntityNode } from '../../components/nodes/er/EntityNode/EntityNode';
import { ClassNode } from '../../components/nodes/uml/ClassNode/ClassNode';
import { TaskNode } from '../../components/nodes/bpmn/TaskNode/TaskNode';
import { EventNode } from '../../components/nodes/bpmn/EventNode/EventNode';
import { GatewayNode } from '../../components/nodes/bpmn/GatewayNode/GatewayNode';
import { PoolNode } from '../../components/nodes/bpmn/PoolNode/PoolNode';

// Import edge components
import {
  AssociationEdge,
  GeneralizationEdge,
  DependencyEdge,
  AggregationEdge,
  CompositionEdge,
  RealizationEdge,
  MessageEdge,
  TransitionEdge,
} from '../../components/edges/uml/UMLEdges';
import { BaseEdge } from '../../components/edges/base/BaseEdge';

// Node type registry
export const nodeTypes: NodeTypes = {
  // ER Nodes
  ER_ENTITY: EntityNode,
  ER_WEAK_ENTITY: EntityNode,
  ER_ATTRIBUTE: EntityNode,

  // UML Nodes
  UML_CLASS: ClassNode,
  UML_INTERFACE: ClassNode,
  UML_ABSTRACT_CLASS: ClassNode,
  UML_PACKAGE: ClassNode,
  UML_COMPONENT: ClassNode,
  UML_NOTE: ClassNode,

  // BPMN Nodes
  BPMN_TASK: TaskNode,
  BPMN_USER_TASK: TaskNode,
  BPMN_SERVICE_TASK: TaskNode,
  BPMN_MANUAL_TASK: TaskNode,
  BPMN_SCRIPT_TASK: TaskNode,
  BPMN_START_EVENT: EventNode,
  BPMN_END_EVENT: EventNode,
  BPMN_INTERMEDIATE_EVENT: EventNode,
  BPMN_GATEWAY_EXCLUSIVE: GatewayNode,
  BPMN_GATEWAY_PARALLEL: GatewayNode,
  BPMN_GATEWAY_INCLUSIVE: GatewayNode,
  BPMN_POOL: PoolNode,
  BPMN_LANE: PoolNode,
};

// Edge type registry with proper typing
export const edgeTypes: EdgeTypes = {
  // ER Edges
  ER_RELATIONSHIP: BaseEdge as ComponentType<EdgeProps>,
  ER_ATTRIBUTE_LINK: BaseEdge as ComponentType<EdgeProps>,

  // UML Edges
  UML_ASSOCIATION: AssociationEdge as ComponentType<EdgeProps>,
  UML_AGGREGATION: AggregationEdge as ComponentType<EdgeProps>,
  UML_COMPOSITION: CompositionEdge as ComponentType<EdgeProps>,
  UML_GENERALIZATION: GeneralizationEdge as ComponentType<EdgeProps>,
  UML_DEPENDENCY: DependencyEdge as ComponentType<EdgeProps>,
  UML_REALIZATION: RealizationEdge as ComponentType<EdgeProps>,
  UML_MESSAGE: MessageEdge as ComponentType<EdgeProps>,
  UML_TRANSITION: TransitionEdge as ComponentType<EdgeProps>,

  // BPMN Edges
  BPMN_SEQUENCE_FLOW: BaseEdge as ComponentType<EdgeProps>,
  BPMN_MESSAGE_FLOW: MessageEdge as ComponentType<EdgeProps>,
  BPMN_ASSOCIATION: BaseEdge as ComponentType<EdgeProps>,
  BPMN_DATA_ASSOCIATION: BaseEdge as ComponentType<EdgeProps>,
};

// Helper function to create default node data based on type
export const createDefaultNodeData = (nodeType: string, position: { x: number; y: number }) => {
  const baseData = {
    label: 'New Node',
    position,
  };

  // ER Nodes
  if (nodeType.startsWith('ER_')) {
    if (nodeType === 'ER_ENTITY' || nodeType === 'ER_WEAK_ENTITY') {
      return {
        ...baseData,
        label: 'New Entity',
        entity: {
          id: `entity_${Date.now()}`,
          name: 'New Entity',
          attributes: [],
          isWeak: nodeType === 'ER_WEAK_ENTITY',
        },
      };
    }
  }

  // UML Nodes
  if (nodeType.startsWith('UML_')) {
    if (nodeType === 'UML_CLASS' || nodeType === 'UML_INTERFACE' || nodeType === 'UML_ABSTRACT_CLASS') {
      return {
        ...baseData,
        label: nodeType === 'UML_INTERFACE' ? 'New Interface' : 'New Class',
        isAbstract: nodeType === 'UML_ABSTRACT_CLASS',
        stereotype: nodeType === 'UML_INTERFACE' ? 'interface' : undefined,
        class: {
          id: `class_${Date.now()}`,
          name: nodeType === 'UML_INTERFACE' ? 'New Interface' : 'New Class',
          attributes: [],
          methods: [],
          isAbstract: nodeType === 'UML_ABSTRACT_CLASS',
        },
      };
    }
  }

  // BPMN Nodes
  if (nodeType.startsWith('BPMN_')) {
    if (nodeType.includes('TASK')) {
      const taskTypeMap: Record<string, any> = {
        BPMN_TASK: 'task',
        BPMN_USER_TASK: 'userTask',
        BPMN_SERVICE_TASK: 'serviceTask',
        BPMN_MANUAL_TASK: 'manualTask',
        BPMN_SCRIPT_TASK: 'scriptTask',
      };

      return {
        ...baseData,
        label: 'New Task',
        task: {
          id: `task_${Date.now()}`,
          name: 'New Task',
          type: taskTypeMap[nodeType] || 'task',
        },
      };
    }

    if (nodeType.includes('EVENT')) {
      const eventTypeMap: Record<string, any> = {
        BPMN_START_EVENT: 'start',
        BPMN_END_EVENT: 'end',
        BPMN_INTERMEDIATE_EVENT: 'intermediate',
      };

      return {
        ...baseData,
        label: '',
        event: {
          id: `event_${Date.now()}`,
          name: '',
          eventType: eventTypeMap[nodeType] || 'start',
        },
      };
    }

    if (nodeType.includes('GATEWAY')) {
      const gatewayTypeMap: Record<string, any> = {
        BPMN_GATEWAY_EXCLUSIVE: 'exclusive',
        BPMN_GATEWAY_PARALLEL: 'parallel',
        BPMN_GATEWAY_INCLUSIVE: 'inclusive',
      };

      return {
        ...baseData,
        label: '',
        gateway: {
          id: `gateway_${Date.now()}`,
          name: '',
          gatewayType: gatewayTypeMap[nodeType] || 'exclusive',
        },
      };
    }

    if (nodeType === 'BPMN_POOL') {
      return {
        ...baseData,
        label: 'New Pool',
        pool: {
          id: `pool_${Date.now()}`,
          name: 'New Pool',
          lanes: [
            { id: `lane_${Date.now()}_1`, name: 'Lane 1', height: 200 },
            { id: `lane_${Date.now()}_2`, name: 'Lane 2', height: 200 },
          ],
        },
      };
    }
  }

  return baseData;
};