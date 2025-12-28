import { Node, Edge } from 'reactflow';

// Diagram Types
export enum DiagramType {
  ER = 'ER',
  UML_CLASS = 'UML_CLASS',
  UML_SEQUENCE = 'UML_SEQUENCE',
  UML_ACTIVITY = 'UML_ACTIVITY',
  UML_STATE = 'UML_STATE',
  UML_COMPONENT = 'UML_COMPONENT',
  UML_DEPLOYMENT = 'UML_DEPLOYMENT',
  BPMN = 'BPMN'
}

// Node Types
export enum ERNodeType {
  ENTITY = 'ER_ENTITY',
  WEAK_ENTITY = 'ER_WEAK_ENTITY',
  ATTRIBUTE = 'ER_ATTRIBUTE',
  KEY_ATTRIBUTE = 'ER_KEY_ATTRIBUTE',
  MULTIVALUED_ATTRIBUTE = 'ER_MULTIVALUED_ATTRIBUTE'
}

export enum UMLNodeType {
  CLASS = 'UML_CLASS',
  INTERFACE = 'UML_INTERFACE',
  ABSTRACT_CLASS = 'UML_ABSTRACT_CLASS',
  PACKAGE = 'UML_PACKAGE',
  COMPONENT = 'UML_COMPONENT',
  NOTE = 'UML_NOTE',
  ACTOR = 'UML_ACTOR',
  USECASE = 'UML_USECASE',
  STATE = 'UML_STATE',
  INITIAL_STATE = 'UML_INITIAL_STATE',
  FINAL_STATE = 'UML_FINAL_STATE',
  ACTIVITY = 'UML_ACTIVITY',
  DECISION = 'UML_DECISION',
  FORK = 'UML_FORK',
  JOIN = 'UML_JOIN'
}

export enum BPMNNodeType {
  TASK = 'BPMN_TASK',
  USER_TASK = 'BPMN_USER_TASK',
  SERVICE_TASK = 'BPMN_SERVICE_TASK',
  MANUAL_TASK = 'BPMN_MANUAL_TASK',
  SCRIPT_TASK = 'BPMN_SCRIPT_TASK',
  START_EVENT = 'BPMN_START_EVENT',
  END_EVENT = 'BPMN_END_EVENT',
  INTERMEDIATE_EVENT = 'BPMN_INTERMEDIATE_EVENT',
  GATEWAY_EXCLUSIVE = 'BPMN_GATEWAY_EXCLUSIVE',
  GATEWAY_PARALLEL = 'BPMN_GATEWAY_PARALLEL',
  GATEWAY_INCLUSIVE = 'BPMN_GATEWAY_INCLUSIVE',
  POOL = 'BPMN_POOL',
  LANE = 'BPMN_LANE',
  DATA_OBJECT = 'BPMN_DATA_OBJECT'
}

// Edge Types
export enum EREdgeType {
  RELATIONSHIP = 'ER_RELATIONSHIP',
  ATTRIBUTE_LINK = 'ER_ATTRIBUTE_LINK'
}

export enum UMLEdgeType {
  ASSOCIATION = 'UML_ASSOCIATION',
  AGGREGATION = 'UML_AGGREGATION',
  COMPOSITION = 'UML_COMPOSITION',
  GENERALIZATION = 'UML_GENERALIZATION',
  DEPENDENCY = 'UML_DEPENDENCY',
  REALIZATION = 'UML_REALIZATION',
  MESSAGE = 'UML_MESSAGE',
  TRANSITION = 'UML_TRANSITION'
}

export enum BPMNEdgeType {
  SEQUENCE_FLOW = 'BPMN_SEQUENCE_FLOW',
  MESSAGE_FLOW = 'BPMN_MESSAGE_FLOW',
  ASSOCIATION = 'BPMN_ASSOCIATION',
  DATA_ASSOCIATION = 'BPMN_DATA_ASSOCIATION'
}

// ER Diagram Specific
export interface ERAttribute {
  id: string;
  name: string;
  type: string;
  isPrimary?: boolean;
  isForeign?: boolean;
  isUnique?: boolean;
  isNullable?: boolean;
  defaultValue?: string;
  isPrimaryKey?: boolean;
  isForeignKey?: boolean;
}

export interface EREntity {
  id: string;
  name: string;
  attributes: ERAttribute[];
  isWeak?: boolean;
}

export interface ERRelationship {
  id: string;
  name: string;
  cardinality: '1:1' | '1:N' | 'N:1' | 'N:M';
  sourceEntity: string;
  targetEntity: string;
  sourceCardinality?: string;  // '1', 'N', '0..1', '1..N', '0..N', 'M'
  targetCardinality?: string;  // '1', 'N', '0..1', '1..N', '0..N', 'M'
  isIdentifying?: boolean;
  color?: string;
  strokeWidth?: number;
  zIndex?: number;
}

// UML Class Diagram Specific
export interface UMLAttribute {
  id: string;
  name: string;
  type: string;
  visibility: 'public' | 'private' | 'protected' | 'package';
  isStatic?: boolean;
  isFinal?: boolean;
}

export interface UMLMethod {
  id: string;
  name: string;
  returnType: string;
  parameters: Array<{ name: string; type: string }>;
  visibility: 'public' | 'private' | 'protected' | 'package';
  isStatic?: boolean;
  isAbstract?: boolean;
}

export interface UMLClass {
  id: string;
  name: string;
  stereotype?: string;
  isAbstract?: boolean;
  attributes: UMLAttribute[];
  methods: UMLMethod[];
}

// BPMN Specific
export interface BPMNTask {
  id: string;
  name: string;
  type: 'task' | 'userTask' | 'serviceTask' | 'manualTask' | 'scriptTask';
  assignee?: string;
  documentation?: string;
}

export interface BPMNEvent {
  id: string;
  name: string;
  eventType: 'start' | 'end' | 'intermediate';
  eventDefinition?: 'message' | 'timer' | 'error' | 'signal' | 'conditional';
}

export interface BPMNGateway {
  id: string;
  name: string;
  gatewayType: 'exclusive' | 'parallel' | 'inclusive' | 'eventBased';
}

export interface BPMNPool {
  id: string;
  name: string;
  lanes: BPMNLane[];
}

export interface BPMNLane {
  id: string;
  name: string;
  height: number;
}

// Base Node Data
export interface BaseNodeData {
  label: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface ERNodeData extends BaseNodeData {
  entity?: EREntity;
  attribute?: ERAttribute;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

export interface UMLNodeData extends BaseNodeData {
  class?: UMLClass;
  stereotype?: string;
  isAbstract?: boolean;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

export interface BPMNNodeData extends BaseNodeData {
  task?: BPMNTask;
  event?: BPMNEvent;
  gateway?: BPMNGateway;
  pool?: BPMNPool;
  lane?: BPMNLane;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

// Diagram Node and Edge Types
export type DiagramNode = Node<ERNodeData | UMLNodeData | BPMNNodeData>;
export type DiagramEdge = Edge;

// Diagram State
export interface DiagramState {
  id: string;
  name: string;
  type: DiagramType;
  modelId: string;
  workspaceId: string;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// Diagram Actions
export interface DiagramAction {
  type: string;
  payload: any;
  timestamp: number;
}

// Layout Options
export interface LayoutOptions {
  algorithm: 'manual' | 'layered' | 'force' | 'swimlane' | 'sequence';
  direction?: 'TB' | 'BT' | 'LR' | 'RL';
  spacing?: {
    nodeSpacing?: number;
    rankSpacing?: number;
    edgeSpacing?: number;
  };
  alignment?: 'UL' | 'UR' | 'DL' | 'DR';
}

// Validation Result
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  id: string;
  nodeId?: string;
  edgeId?: string;
  message: string;
  severity: 'error';
}

export interface ValidationWarning {
  id: string;
  nodeId?: string;
  edgeId?: string;
  message: string;
  severity: 'warning';
}