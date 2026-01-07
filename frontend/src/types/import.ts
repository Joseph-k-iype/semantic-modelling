// frontend/src/types/import.ts
/**
 * Type definitions for Data Import feature
 */

// ============================================================================
// NODE TYPES
// ============================================================================

export type NodeType = 'package' | 'class' | 'object' | 'interface' | 'enumeration';
export type EdgeType = 'association' | 'aggregation' | 'composition' | 'generalization' | 'realization' | 'dependency';
export type Visibility = '+' | '-' | '#' | '~';
export type FileType = 'csv' | 'excel' | 'json';
export type LayoutAlgorithm = 'hierarchical' | 'force' | 'circular' | 'grid';

// ============================================================================
// TEMPLATE STRUCTURES
// ============================================================================

export interface AttributeTemplate {
  name: string;
  type: string;
  visibility: Visibility;
  is_static?: boolean;
  default_value?: string;
}

export interface MethodTemplate {
  name: string;
  return_type: string;
  parameters: string[];
  visibility: Visibility;
  is_static?: boolean;
  is_abstract?: boolean;
}

export interface LiteralTemplate {
  name: string;
  value?: string;
}

export interface NodeTemplate {
  id: string;
  type: NodeType;
  label: string;
  attributes?: AttributeTemplate[];
  methods?: MethodTemplate[];
  literals?: LiteralTemplate[];
  parent_package_id?: string;
  stereotype?: string;
  is_abstract?: boolean;
  description?: string;
  x?: number;
  y?: number;
}

export interface EdgeTemplate {
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
  source_multiplicity?: string;
  target_multiplicity?: string;
  is_navigable?: boolean;
  description?: string;
}

export interface ImportTemplate {
  nodes: NodeTemplate[];
  edges: EdgeTemplate[];
}

// ============================================================================
// FILE UPLOAD & PREVIEW
// ============================================================================

export interface FilePreviewData {
  columns?: string[];
  row_count?: number;
  sample_rows?: Record<string, any>[];
  sheets?: string[];
  sheets_data?: Record<string, SheetData>;
  structure?: JsonStructure;
  sample?: any;
}

export interface SheetData {
  columns: string[];
  row_count: number;
  sample_rows: Record<string, any>[];
}

export interface JsonStructure {
  type: string;
  keys?: Record<string, any>;
  length?: number;
  item_structure?: any;
  truncated?: boolean;
}

export interface DetectedStructure {
  suggestions: Record<string, any>;
  format: string;
  recommended_node_mapping?: Record<string, string>;
  recommended_nodes_sheet?: string;
  recommended_edges_sheet?: string;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: FileType;
  preview_data: FilePreviewData;
  detected_structure: DetectedStructure;
}

// ============================================================================
// MAPPING CONFIGURATION
// ============================================================================

export interface ColumnMapping {
  source_column: string;
  target_field: string;
  transformation?: string;
}

export interface NodeMappingConfig {
  node_type: NodeType;
  id_column?: string;
  label_column: string;
  attribute_columns?: string[];
  method_columns?: string[];
  literal_columns?: string[];
  column_mappings?: ColumnMapping[];
  filter_expression?: string;
}

export interface EdgeMappingConfig {
  edge_type: EdgeType;
  source_column: string;
  target_column: string;
  label_column?: string;
  source_multiplicity_column?: string;
  target_multiplicity_column?: string;
}

export interface ImportMappingConfig {
  file_id: string;
  diagram_name: string;
  workspace_name: string;
  sheet_name?: string;
  data_path?: string;
  node_mappings: NodeMappingConfig[];
  edge_mappings: EdgeMappingConfig[];
  auto_layout: boolean;
  layout_algorithm: LayoutAlgorithm;
}

// ============================================================================
// PREVIEW & EXECUTION
// ============================================================================

export interface ImportPreviewResponse {
  total_nodes: number;
  total_edges: number;
  node_type_counts: Record<string, number>;
  edge_type_counts: Record<string, number>;
  preview_nodes: NodeTemplate[];
  preview_edges: EdgeTemplate[];
  warnings: string[];
  errors: string[];
}

export interface ImportExecutionResponse {
  success: boolean;
  diagram_id: string;
  nodes_imported: number;
  edges_imported: number;
  warnings: string[];
  errors: string[];
}

// ============================================================================
// TEMPLATE INFO
// ============================================================================

export interface TemplateInfo {
  description: string;
  supported_node_types: string[];
  supported_edge_types: string[];
  template_structure: any;
  examples: Record<string, any>;
}

export interface ImportExamples {
  csv_examples: Record<string, CsvExample>;
  json_example: JsonExample;
}

export interface CsvExample {
  description: string;
  csv_content: string;
  edges_csv?: string;
}

export interface JsonExample {
  description: string;
  content: ImportTemplate;
}

// ============================================================================
// UI STATE TYPES
// ============================================================================

export type ImportStep = 'upload' | 'mapping' | 'preview' | 'complete';

export interface ImportState {
  step: ImportStep;
  file: File | null;
  fileId: string;
  filePreview: FileUploadResponse | null;
  mappingConfig: ImportMappingConfig | null;
  previewData: ImportPreviewResponse | null;
  importResult: ImportExecutionResponse | null;
  loading: boolean;
  error: string;
  uploadProgress: number;
}

// ============================================================================
// VALIDATION TYPES
// ============================================================================

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export interface NodeTypeInfo {
  type: NodeType;
  label: string;
  description: string;
  icon: string;
  supportsAttributes: boolean;
  supportsMethods: boolean;
  supportsLiterals: boolean;
}

export interface EdgeTypeInfo {
  type: EdgeType;
  label: string;
  description: string;
  icon: string;
  supportsMultiplicity: boolean;
}