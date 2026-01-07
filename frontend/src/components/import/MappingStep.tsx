// frontend/src/components/import/MappingStep.tsx
/**
 * Mapping configuration step component
 */

import React, { useState, useEffect } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import {
  FileUploadResponse,
  ImportMappingConfig,
  NodeType,
  LayoutAlgorithm,
} from '../../types/import';
import { NODE_TYPE_INFO, validateDiagramName, validateWorkspaceName } from '../../utils/importUtils';

interface MappingStepProps {
  filePreview: FileUploadResponse;
  fileId: string;
  onGeneratePreview: (config: ImportMappingConfig) => Promise<void>;
  loading: boolean;
  onBack: () => void;
}

const MappingStep: React.FC<MappingStepProps> = ({
  filePreview,
  fileId,
  onGeneratePreview,
  loading,
  onBack,
}) => {
  const [diagramName, setDiagramName] = useState('');
  const [workspaceName, setWorkspaceName] = useState('default');
  const [nodeType, setNodeType] = useState<NodeType>('class');
  const [labelColumn, setLabelColumn] = useState('');
  const [idColumn, setIdColumn] = useState('');
  const [attributeColumns, setAttributeColumns] = useState<string[]>([]);
  const [methodColumns, setMethodColumns] = useState<string[]>([]);
  const [autoLayout, setAutoLayout] = useState(true);
  const [layoutAlgorithm, setLayoutAlgorithm] = useState<LayoutAlgorithm>('hierarchical');
  const [errors, setErrors] = useState<string[]>([]);

  const columns = filePreview.preview_data.columns || [];
  const selectedNodeTypeInfo = NODE_TYPE_INFO[nodeType];

  // Auto-select recommended columns
  useEffect(() => {
    const detected = filePreview.detected_structure;
    if (detected.recommended_node_mapping) {
      if (detected.recommended_node_mapping.label_column) {
        setLabelColumn(detected.recommended_node_mapping.label_column);
      }
      if (detected.recommended_node_mapping.id_column) {
        setIdColumn(detected.recommended_node_mapping.id_column);
      }
    }

    // Try to find common column names
    const labelCandidates = ['label', 'name', 'title'];
    const idCandidates = ['id', 'identifier', 'key'];
    const attrCandidates = ['attributes', 'attrs', 'fields'];
    const methodCandidates = ['methods', 'functions', 'operations'];

    if (!labelColumn) {
      const found = columns.find((col) =>
        labelCandidates.some((c) => col.toLowerCase().includes(c))
      );
      if (found) setLabelColumn(found);
    }

    if (!idColumn) {
      const found = columns.find((col) => idCandidates.some((c) => col.toLowerCase() === c));
      if (found) setIdColumn(found);
    }

    if (attributeColumns.length === 0) {
      const found = columns.filter((col) =>
        attrCandidates.some((c) => col.toLowerCase().includes(c))
      );
      if (found.length > 0) setAttributeColumns(found);
    }

    if (methodColumns.length === 0) {
      const found = columns.filter((col) =>
        methodCandidates.some((c) => col.toLowerCase().includes(c))
      );
      if (found.length > 0) setMethodColumns(found);
    }
  }, [filePreview, columns, labelColumn, idColumn, attributeColumns.length, methodColumns.length]);

  const handleSubmit = () => {
    // Validate
    const validationErrors: string[] = [];

    const nameError = validateDiagramName(diagramName);
    if (nameError) validationErrors.push(nameError);

    const workspaceError = validateWorkspaceName(workspaceName);
    if (workspaceError) validationErrors.push(workspaceError);

    if (!labelColumn) {
      validationErrors.push('Label column is required');
    }

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors([]);

    // Build configuration
    const config: ImportMappingConfig = {
      file_id: fileId,
      diagram_name: diagramName,
      workspace_name: workspaceName,
      node_mappings: [
        {
          node_type: nodeType,
          label_column: labelColumn,
          id_column: idColumn || undefined,
          attribute_columns:
            attributeColumns.length > 0 && selectedNodeTypeInfo.supportsAttributes
              ? attributeColumns
              : undefined,
          method_columns:
            methodColumns.length > 0 && selectedNodeTypeInfo.supportsMethods
              ? methodColumns
              : undefined,
        },
      ],
      edge_mappings: [],
      auto_layout: autoLayout,
      layout_algorithm: layoutAlgorithm,
    };

    onGeneratePreview(config);
  };

  const toggleColumn = (column: string, list: string[], setter: (val: string[]) => void) => {
    if (list.includes(column)) {
      setter(list.filter((c) => c !== column));
    } else {
      setter([...list, column]);
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Configure Data Mapping</h2>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="font-semibold text-red-900 mb-2">Please fix the following errors:</p>
          <ul className="list-disc list-inside space-y-1">
            {errors.map((error, idx) => (
              <li key={idx} className="text-red-700 text-sm">
                {error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Diagram Settings */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Diagram Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Diagram Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={diagramName}
              onChange={(e) => setDiagramName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              placeholder="My Imported Diagram"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Workspace Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              placeholder="default"
            />
          </div>
        </div>
      </div>

      {/* Node Mapping */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Node Mapping</h3>

        <div className="space-y-4">
          {/* Node Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Node Type <span className="text-red-500">*</span>
            </label>
            <select
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value as NodeType)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              {Object.values(NODE_TYPE_INFO).map((info) => (
                <option key={info.type} value={info.type}>
                  {info.icon} {info.label} - {info.description}
                </option>
              ))}
            </select>
          </div>

          {/* Label Column */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Label Column <span className="text-red-500">*</span>
              <span className="text-gray-500 text-xs ml-2">(used as node name)</span>
            </label>
            <select
              value={labelColumn}
              onChange={(e) => setLabelColumn(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value="">Select column...</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          {/* ID Column */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID Column <span className="text-gray-500 text-xs">(optional, will auto-generate if not specified)</span>
            </label>
            <select
              value={idColumn}
              onChange={(e) => setIdColumn(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value="">Auto-generate</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          {/* Attribute Columns */}
          {selectedNodeTypeInfo.supportsAttributes && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Attribute Columns
                <span className="text-gray-500 text-xs ml-2">
                  (select columns containing attributes)
                </span>
              </label>
              <div className="border border-gray-300 rounded-lg p-4 max-h-48 overflow-y-auto">
                {columns.map((col) => (
                  <label
                    key={col}
                    className="flex items-center py-2 hover:bg-gray-50 cursor-pointer rounded px-2"
                  >
                    <input
                      type="checkbox"
                      checked={attributeColumns.includes(col)}
                      onChange={() => toggleColumn(col, attributeColumns, setAttributeColumns)}
                      className="mr-3"
                    />
                    <span className="text-sm">{col}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Method Columns */}
          {selectedNodeTypeInfo.supportsMethods && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Method Columns
                <span className="text-gray-500 text-xs ml-2">(select columns containing methods)</span>
              </label>
              <div className="border border-gray-300 rounded-lg p-4 max-h-48 overflow-y-auto">
                {columns.map((col) => (
                  <label
                    key={col}
                    className="flex items-center py-2 hover:bg-gray-50 cursor-pointer rounded px-2"
                  >
                    <input
                      type="checkbox"
                      checked={methodColumns.includes(col)}
                      onChange={() => toggleColumn(col, methodColumns, setMethodColumns)}
                      className="mr-3"
                    />
                    <span className="text-sm">{col}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Layout Options */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Layout Options</h3>
        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoLayout}
              onChange={(e) => setAutoLayout(e.target.checked)}
              className="mr-3"
            />
            <span className="text-sm">Automatically arrange nodes</span>
          </label>

          {autoLayout && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Layout Algorithm
              </label>
              <select
                value={layoutAlgorithm}
                onChange={(e) => setLayoutAlgorithm(e.target.value as LayoutAlgorithm)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                <option value="hierarchical">Hierarchical - Best for class hierarchies</option>
                <option value="force">Force-Directed - Natural spacing</option>
                <option value="circular">Circular - Equal relationships</option>
                <option value="grid">Grid - Simple row/column layout</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Data Preview */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Data Preview</h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filePreview.preview_data.sample_rows?.slice(0, 3).map((row, idx) => (
                  <tr key={idx}>
                    {columns.map((col) => (
                      <td key={col} className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Showing 3 of {filePreview.preview_data.row_count || 0} rows
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          disabled={loading}
          className="inline-flex items-center px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ArrowLeft size={18} className="mr-2" />
          Back
        </button>
        <button
          onClick={handleSubmit}
          disabled={!diagramName || !labelColumn || loading}
          className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Generating Preview...' : 'Generate Preview'}
          <ArrowRight size={18} className="ml-2" />
        </button>
      </div>
    </div>
  );
};

export default MappingStep;