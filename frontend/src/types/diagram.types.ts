/**
 * Diagram Type Definitions - Simplified for UML Only
 * Path: frontend/src/types/diagram.types.ts
 */

import { Node, Edge } from 'reactflow';

// ============================================================================
// ELEMENT TYPES (5 types only)
// ============================================================================

export enum NodeType {
  PACKAGE = 'package',
  CLASS = 'class',
  OBJECT = 'object',
  INTERFACE = 'interface',
  ENUMERATION = 'enumeration'
}

export enum RelationshipType {
  ASSOCIATION = 'Association',
  COMPOSITION = 'Composition',
  AGGREGATION = 'Aggregation',
  INHERITANCE = 'Inheritance',
  DEPENDENCY = 'Dependency',
  REALIZATION = 'Realization'
}

// ============================================================================
// ATTRIBUTE & METHOD TYPES
// ============================================================================

export interface Attribute {
  id: string;
  name: string;
  dataType: string;
  key?: 'PRIMARY KEY' | 'FOREIGN KEY' | 'Default';
  visibility?: 'public' | 'private' | 'protected' | 'package';
  isStatic?: boolean;
  isFinal?: boolean;
  defaultValue?: string;
}

export interface Method {
  id: string;
  name: string;
  returnType: string;
  parameters: Array<{ name: string; type: string }>;
  visibility?: 'public' | 'private' | 'protected' | 'package';
  isStatic?: boolean;
  isAbstract?: boolean;
}

// ============================================================================
// NODE DATA INTERFACES
// ============================================================================

export interface BaseNodeData {
  label: string;
  stereotype?: string;
  description?: string;
  color: string;
  parentId?: string; // For package membership
  zIndex?: number;
}

export interface PackageNodeData extends BaseNodeData {
  type: NodeType.PACKAGE;
}

export interface ClassNodeData extends BaseNodeData {
  type: NodeType.CLASS;
  attributes: Attribute[];
  methods?: Method[];
  isAbstract?: boolean;
}

export interface ObjectNodeData extends BaseNodeData {
  type: NodeType.OBJECT;
  attributes: Attribute[];
}

export interface InterfaceNodeData extends BaseNodeData {
  type: NodeType.INTERFACE;
  methods?: Method[];
}

export interface EnumerationNodeData extends BaseNodeData {
  type: NodeType.ENUMERATION;
  literals: string[]; // e.g., ['SMALL', 'MEDIUM', 'LARGE']
}

export type NodeData = 
  | PackageNodeData 
  | ClassNodeData 
  | ObjectNodeData 
  | InterfaceNodeData 
  | EnumerationNodeData;

// ============================================================================
// EDGE DATA INTERFACES
// ============================================================================

export interface EdgeData {
  type: RelationshipType;
  sourceCardinality: string; // e.g., '1', '0..1', '1..*', '*'
  targetCardinality: string;
  label?: string;
  color?: string;
  strokeWidth?: number;
  isIdentifying?: boolean;
}

// ============================================================================
// DIAGRAM STATE
// ============================================================================

export interface DiagramState {
  id: string;
  name: string;
  workspaceName: string;
  graphName: string; // FalkorDB graph reference
  nodes: Node<NodeData>[];
  edges: Edge<EdgeData>[];
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
  isPublished: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// ============================================================================
// API TYPES
// ============================================================================

export interface CreateDiagramRequest {
  workspace_name: string;
  name: string;
}

export interface CreateDiagramResponse {
  id: string;
  name: string;
  workspace_name: string;
  graph_name: string;
  created_at: string;
  updated_at: string;
}

export interface PublishedModel {
  id: string;
  name: string;
  workspace_name: string;
  author_name: string;
  total_classes: number;
  total_relationships: number;
  created_at: string;
  updated_at: string;
}

export interface SaveDiagramRequest {
  nodes: Node<NodeData>[];
  edges: Edge<EdgeData>[];
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
}

export interface SyncToFalkorDBRequest {
  diagram_id: string;
  nodes: Array<{
    id: string;
    type: string;
    data: NodeData;
    position: { x: number; y: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    data: EdgeData;
  }>;
}

// ============================================================================
// CARDINALITY OPTIONS
// ============================================================================

export const CARDINALITY_OPTIONS = [
  { value: '0..1', label: '0..1 (Zero or One)' },
  { value: '1', label: '1 (Exactly One)' },
  { value: '0..*', label: '0..* (Zero or Many)' },
  { value: '1..*', label: '1..* (One or Many)' },
  { value: '*', label: '* (Many)' },
] as const;

// ============================================================================
// RELATIONSHIP TYPE OPTIONS
// ============================================================================

export const RELATIONSHIP_TYPE_OPTIONS = [
  { 
    value: RelationshipType.ASSOCIATION, 
    label: 'Association',
    description: 'A structural relationship that describes a connection between objects'
  },
  { 
    value: RelationshipType.COMPOSITION, 
    label: 'Composition',
    description: 'A strong "whole-part" relationship where the part cannot exist without the whole'
  },
  { 
    value: RelationshipType.AGGREGATION, 
    label: 'Aggregation',
    description: 'A weak "whole-part" relationship where the part can exist independently'
  },
  { 
    value: RelationshipType.INHERITANCE, 
    label: 'Inheritance',
    description: 'An "is-a" relationship representing generalization/specialization'
  },
  { 
    value: RelationshipType.DEPENDENCY, 
    label: 'Dependency',
    description: 'A relationship where one element depends on another'
  },
  { 
    value: RelationshipType.REALIZATION, 
    label: 'Realization',
    description: 'A relationship between an interface and a class that implements it'
  },
] as const;

// ============================================================================
// DATA TYPE OPTIONS
// ============================================================================

export const DATA_TYPE_OPTIONS = [
  'INTEGER',
  'VARCHAR',
  'TEXT',
  'BOOLEAN',
  'DATE',
  'TIMESTAMP',
  'DECIMAL',
  'FLOAT',
  'DOUBLE',
  'BIGINT',
  'SMALLINT',
  'CHAR',
  'UUID',
  'JSON',
  'ARRAY',
] as const;

// ============================================================================
// KEY TYPE OPTIONS
// ============================================================================

export const KEY_TYPE_OPTIONS = [
  { value: 'PRIMARY KEY', label: 'PK', description: 'Primary Key' },
  { value: 'FOREIGN KEY', label: 'FK', description: 'Foreign Key' },
  { value: 'Default', label: 'ID', description: 'Regular Attribute' },
] as const;