// frontend/src/components/import/PreviewStep.tsx
/**
 * Preview step component
 */

import React from 'react';
import { ArrowLeft, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { ImportPreviewResponse, NodeTemplate } from '../../types/import';
import { NODE_TYPE_INFO, formatPreviewSummary } from '../../utils/importUtils';

interface PreviewStepProps {
  previewData: ImportPreviewResponse;
  onExecute: () => Promise<void>;
  onBack: () => void;
  loading: boolean;
}

const PreviewStep: React.FC<PreviewStepProps> = ({ previewData, onExecute, onBack, loading }) => {
  const hasErrors = previewData.errors.length > 0;
  const canExecute = !hasErrors && !loading;

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Import Preview</h2>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Nodes"
          value={previewData.total_nodes}
          color="bg-blue-50"
          textColor="text-blue-700"
        />
        <StatCard
          title="Total Edges"
          value={previewData.total_edges}
          color="bg-green-50"
          textColor="text-green-700"
        />
        <StatCard
          title="Classes"
          value={previewData.node_type_counts['class'] || 0}
          color="bg-purple-50"
          textColor="text-purple-700"
        />
        <StatCard
          title="Interfaces"
          value={previewData.node_type_counts['interface'] || 0}
          color="bg-orange-50"
          textColor="text-orange-700"
        />
      </div>

      {/* Summary Text */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-700">
          <strong>Summary:</strong> {formatPreviewSummary(previewData)}
        </p>
      </div>

      {/* Warnings */}
      {previewData.warnings.length > 0 && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="text-yellow-600 mr-3 mt-0.5 flex-shrink-0" size={20} />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">Warnings</h3>
              <ul className="list-disc list-inside space-y-1">
                {previewData.warnings.map((warning, idx) => (
                  <li key={idx} className="text-yellow-700 text-sm">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Errors */}
      {hasErrors && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="text-red-600 mr-3 mt-0.5 flex-shrink-0" size={20} />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 mb-2">Errors</h3>
              <p className="text-red-700 text-sm mb-2">
                The following errors must be fixed before importing:
              </p>
              <ul className="list-disc list-inside space-y-1">
                {previewData.errors.map((error, idx) => (
                  <li key={idx} className="text-red-700 text-sm">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Node Type Breakdown */}
      {Object.keys(previewData.node_type_counts).length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Node Type Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(previewData.node_type_counts).map(([type, count]) => {
              const info = NODE_TYPE_INFO[type as keyof typeof NODE_TYPE_INFO];
              return (
                <div
                  key={type}
                  className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <span className="text-2xl mr-3">{info?.icon || '📦'}</span>
                  <div>
                    <p className="text-xs text-gray-600">{info?.label || type}</p>
                    <p className="text-xl font-bold text-gray-900">{count}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Node Preview */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">
          Sample Nodes ({Math.min(previewData.preview_nodes.length, 10)} shown)
        </h3>
        <div className="space-y-4">
          {previewData.preview_nodes.slice(0, 10).map((node) => (
            <NodePreviewCard key={node.id} node={node} />
          ))}
        </div>
        {previewData.preview_nodes.length > 10 && (
          <p className="text-sm text-gray-500 mt-4">
            ... and {previewData.preview_nodes.length - 10} more nodes
          </p>
        )}
      </div>

      {/* Edge Preview */}
      {previewData.preview_edges.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">
            Sample Edges ({Math.min(previewData.preview_edges.length, 5)} shown)
          </h3>
          <div className="space-y-3">
            {previewData.preview_edges.slice(0, 5).map((edge, idx) => (
              <div key={idx} className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                <code className="text-sm text-blue-600 font-mono">{edge.source}</code>
                <span className="mx-3 text-gray-400">→</span>
                <code className="text-sm text-blue-600 font-mono">{edge.target}</code>
                <span className="ml-3 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                  {edge.type}
                </span>
                {edge.label && (
                  <span className="ml-2 text-sm text-gray-600">"{edge.label}"</span>
                )}
              </div>
            ))}
          </div>
          {previewData.preview_edges.length > 5 && (
            <p className="text-sm text-gray-500 mt-4">
              ... and {previewData.preview_edges.length - 5} more edges
            </p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onBack}
          disabled={loading}
          className="inline-flex items-center px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ArrowLeft size={18} className="mr-2" />
          Back to Mapping
        </button>
        <button
          onClick={onExecute}
          disabled={!canExecute}
          className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
              Importing...
            </>
          ) : (
            <>
              <CheckCircle size={18} className="mr-2" />
              Execute Import
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// Stat Card Component
interface StatCardProps {
  title: string;
  value: number;
  color: string;
  textColor: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, color, textColor }) => (
  <div className={`${color} rounded-lg p-4 text-center`}>
    <p className="text-sm text-gray-600 mb-1">{title}</p>
    <p className={`text-3xl font-bold ${textColor}`}>{value}</p>
  </div>
);

// Node Preview Card Component
interface NodePreviewCardProps {
  node: NodeTemplate;
}

const NodePreviewCard: React.FC<NodePreviewCardProps> = ({ node }) => {
  const nodeInfo = NODE_TYPE_INFO[node.type];

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
      <div className="flex items-center mb-2">
        <span className="text-xl mr-2">{nodeInfo.icon}</span>
        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded mr-2">
          {nodeInfo.label}
        </span>
        <span className="font-medium text-gray-900">{node.label}</span>
        {node.is_abstract && (
          <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded italic">
            abstract
          </span>
        )}
      </div>

      {node.stereotype && (
        <div className="mb-2">
          <span className="text-xs text-gray-500">«{node.stereotype}»</span>
        </div>
      )}

      {node.attributes && node.attributes.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-600 mb-1 font-medium">Attributes:</p>
          <div className="text-sm text-gray-700 space-y-1 bg-gray-50 p-2 rounded">
            {node.attributes.slice(0, 5).map((attr, idx) => (
              <div key={idx} className="font-mono text-xs">
                <span className="text-blue-600">{attr.visibility}</span> {attr.name}:{' '}
                <span className="text-purple-600">{attr.type}</span>
                {attr.is_static && <span className="ml-1 text-gray-500 italic">static</span>}
              </div>
            ))}
            {node.attributes.length > 5 && (
              <p className="text-xs text-gray-500">... and {node.attributes.length - 5} more</p>
            )}
          </div>
        </div>
      )}

      {node.methods && node.methods.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-600 mb-1 font-medium">Methods:</p>
          <div className="text-sm text-gray-700 space-y-1 bg-gray-50 p-2 rounded">
            {node.methods.slice(0, 3).map((method, idx) => (
              <div key={idx} className="font-mono text-xs">
                <span className="text-blue-600">{method.visibility}</span> {method.name}():{' '}
                <span className="text-purple-600">{method.return_type}</span>
                {method.is_abstract && <span className="ml-1 text-gray-500 italic">abstract</span>}
              </div>
            ))}
            {node.methods.length > 3 && (
              <p className="text-xs text-gray-500">... and {node.methods.length - 3} more</p>
            )}
          </div>
        </div>
      )}

      {node.literals && node.literals.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-600 mb-1 font-medium">Literals:</p>
          <div className="text-sm text-gray-700 space-y-1 bg-gray-50 p-2 rounded">
            {node.literals.map((literal, idx) => (
              <div key={idx} className="font-mono text-xs">
                {literal.name}
                {literal.value && <span className="text-gray-500"> = {literal.value}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewStep;