// frontend/src/utils/importUtils.ts
/**
 * Utility functions for import feature
 */

import { NodeType, EdgeType, NodeTypeInfo, EdgeTypeInfo } from '../types/import';

/**
 * Node type metadata
 */
export const NODE_TYPE_INFO: Record<NodeType, NodeTypeInfo> = {
  package: {
    type: 'package',
    label: 'Package',
    description: 'A container for grouping related elements',
    icon: '📦',
    supportsAttributes: false,
    supportsMethods: false,
    supportsLiterals: false,
  },
  class: {
    type: 'class',
    label: 'Class',
    description: 'A blueprint for objects with attributes and methods',
    icon: '🔷',
    supportsAttributes: true,
    supportsMethods: true,
    supportsLiterals: false,
  },
  object: {
    type: 'object',
    label: 'Object',
    description: 'An instance of a class',
    icon: '⬡',
    supportsAttributes: true,
    supportsMethods: false,
    supportsLiterals: false,
  },
  interface: {
    type: 'interface',
    label: 'Interface',
    description: 'A contract defining methods without implementation',
    icon: '◇',
    supportsAttributes: true,
    supportsMethods: true,
    supportsLiterals: false,
  },
  enumeration: {
    type: 'enumeration',
    label: 'Enumeration',
    description: 'A set of named constant values',
    icon: '▢',
    supportsAttributes: false,
    supportsMethods: false,
    supportsLiterals: true,
  },
};

/**
 * Edge type metadata
 */
export const EDGE_TYPE_INFO: Record<EdgeType, EdgeTypeInfo> = {
  association: {
    type: 'association',
    label: 'Association',
    description: 'A general relationship between classes',
    icon: '→',
    supportsMultiplicity: true,
  },
  aggregation: {
    type: 'aggregation',
    label: 'Aggregation',
    description: 'A "has-a" relationship (weak ownership)',
    icon: '◇→',
    supportsMultiplicity: true,
  },
  composition: {
    type: 'composition',
    label: 'Composition',
    description: 'A "contains" relationship (strong ownership)',
    icon: '◆→',
    supportsMultiplicity: true,
  },
  generalization: {
    type: 'generalization',
    label: 'Generalization',
    description: 'An "is-a" relationship (inheritance)',
    icon: '△→',
    supportsMultiplicity: false,
  },
  realization: {
    type: 'realization',
    label: 'Realization',
    description: 'Implementation of an interface',
    icon: '△⋯→',
    supportsMultiplicity: false,
  },
  dependency: {
    type: 'dependency',
    label: 'Dependency',
    description: 'A "uses" relationship',
    icon: '⋯→',
    supportsMultiplicity: false,
  },
};

/**
 * Validate file type
 */
export const isValidFileType = (filename: string): boolean => {
  const validExtensions = ['.csv', '.xlsx', '.xls', '.json'];
  return validExtensions.some((ext) => filename.toLowerCase().endsWith(ext));
};

/**
 * Get file extension
 */
export const getFileExtension = (filename: string): string => {
  const parts = filename.split('.');
  return parts.length > 1 ? `.${parts[parts.length - 1].toLowerCase()}` : '';
};

/**
 * Format file size
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Parse attribute string
 * Format: "name:type;name2:type2"
 */
export const parseAttributeString = (attrString: string): Array<{ name: string; type: string }> => {
  if (!attrString || !attrString.trim()) {
    return [];
  }

  return attrString
    .split(';')
    .map((attr) => attr.trim())
    .filter((attr) => attr.includes(':'))
    .map((attr) => {
      const [name, type] = attr.split(':');
      return {
        name: name.trim(),
        type: type.trim(),
      };
    });
};

/**
 * Parse method string
 * Format: "methodName(param:Type):ReturnType"
 */
export const parseMethodString = (
  methodString: string
): Array<{ name: string; parameters: string[]; returnType: string }> => {
  if (!methodString || !methodString.trim()) {
    return [];
  }

  return methodString
    .split(';')
    .map((method) => method.trim())
    .filter((method) => method)
    .map((method) => {
      const match = method.match(/^(\w+)\((.*?)\):(\w+)$/);
      if (match) {
        const [, name, params, returnType] = match;
        const parameters = params
          .split(',')
          .map((p) => p.trim())
          .filter((p) => p);
        return {
          name,
          parameters,
          returnType,
        };
      }
      return {
        name: method,
        parameters: [],
        returnType: 'void',
      };
    });
};

/**
 * Validate diagram name
 */
export const validateDiagramName = (name: string): string | null => {
  if (!name || !name.trim()) {
    return 'Diagram name is required';
  }

  if (name.length > 100) {
    return 'Diagram name must be 100 characters or less';
  }

  if (!/^[a-zA-Z0-9\s\-_]+$/.test(name)) {
    return 'Diagram name can only contain letters, numbers, spaces, hyphens, and underscores';
  }

  return null;
};

/**
 * Validate workspace name
 */
export const validateWorkspaceName = (name: string): string | null => {
  if (!name || !name.trim()) {
    return 'Workspace name is required';
  }

  if (name.length > 50) {
    return 'Workspace name must be 50 characters or less';
  }

  if (!/^[a-zA-Z0-9\-_]+$/.test(name)) {
    return 'Workspace name can only contain letters, numbers, hyphens, and underscores';
  }

  return null;
};

/**
 * Generate unique ID
 */
export const generateUniqueId = (prefix: string = 'node'): string => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Get node type color
 */
export const getNodeTypeColor = (type: NodeType): string => {
  const colors: Record<NodeType, string> = {
    package: '#E3F2FD',
    class: '#BBDEFB',
    object: '#90CAF9',
    interface: '#E1BEE7',
    enumeration: '#C5E1A5',
  };
  return colors[type] || '#E0E0E0';
};

/**
 * Get edge type style
 */
export const getEdgeTypeStyle = (type: EdgeType): string => {
  const styles: Record<EdgeType, string> = {
    association: 'solid',
    aggregation: 'solid',
    composition: 'solid',
    generalization: 'solid',
    realization: 'dashed',
    dependency: 'dashed',
  };
  return styles[type] || 'solid';
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.substring(0, maxLength - 3)}...`;
};

/**
 * Check if preview has critical errors
 */
export const hasCriticalErrors = (errors: string[]): boolean => {
  const criticalKeywords = ['not found', 'missing', 'required', 'invalid'];
  return errors.some((error) =>
    criticalKeywords.some((keyword) => error.toLowerCase().includes(keyword))
  );
};

/**
 * Group errors by type
 */
export const groupErrors = (errors: string[]): Record<string, string[]> => {
  const grouped: Record<string, string[]> = {
    node: [],
    edge: [],
    validation: [],
    other: [],
  };

  errors.forEach((error) => {
    const errorLower = error.toLowerCase();
    if (errorLower.includes('node')) {
      grouped.node.push(error);
    } else if (errorLower.includes('edge') || errorLower.includes('relationship')) {
      grouped.edge.push(error);
    } else if (errorLower.includes('invalid') || errorLower.includes('required')) {
      grouped.validation.push(error);
    } else {
      grouped.other.push(error);
    }
  });

  return grouped;
};

/**
 * Calculate import statistics
 */
export const calculateImportStats = (preview: {
  total_nodes: number;
  total_edges: number;
  node_type_counts: Record<string, number>;
}): Array<{ label: string; value: number; color: string }> => {
  return [
    { label: 'Total Nodes', value: preview.total_nodes, color: '#2196F3' },
    { label: 'Total Edges', value: preview.total_edges, color: '#4CAF50' },
    { label: 'Classes', value: preview.node_type_counts['class'] || 0, color: '#FF9800' },
    { label: 'Interfaces', value: preview.node_type_counts['interface'] || 0, color: '#9C27B0' },
  ];
};

/**
 * Format preview summary
 */
export const formatPreviewSummary = (preview: {
  total_nodes: number;
  total_edges: number;
  warnings: string[];
  errors: string[];
}): string => {
  const parts: string[] = [];

  parts.push(`${preview.total_nodes} node${preview.total_nodes !== 1 ? 's' : ''}`);
  parts.push(`${preview.total_edges} edge${preview.total_edges !== 1 ? 's' : ''}`);

  if (preview.warnings.length > 0) {
    parts.push(`${preview.warnings.length} warning${preview.warnings.length !== 1 ? 's' : ''}`);
  }

  if (preview.errors.length > 0) {
    parts.push(`${preview.errors.length} error${preview.errors.length !== 1 ? 's' : ''}`);
  }

  return parts.join(', ');
};

/**
 * Get recommended layout for node count
 */
export const getRecommendedLayout = (nodeCount: number): 'hierarchical' | 'force' | 'circular' | 'grid' => {
  if (nodeCount <= 5) return 'circular';
  if (nodeCount <= 15) return 'hierarchical';
  if (nodeCount <= 50) return 'force';
  return 'grid';
};

/**
 * Sanitize filename
 */
export const sanitizeFilename = (filename: string): string => {
  return filename.replace(/[^a-zA-Z0-9\-_.]/g, '_');
};