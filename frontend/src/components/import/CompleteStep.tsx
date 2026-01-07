// frontend/src/components/import/CompleteStep.tsx
/**
 * Import complete step component
 */

import React from 'react';
import { CheckCircle, ExternalLink, RefreshCw, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ImportExecutionResponse } from '../../types/import';

interface CompleteStepProps {
  importResult: ImportExecutionResponse;
  onReset: () => void;
}

const CompleteStep: React.FC<CompleteStepProps> = ({ importResult, onReset }) => {
  const navigate = useNavigate();

  const handleViewDiagram = () => {
    // Navigate to ontology builder with the diagram ID
    navigate(`/ontology/${importResult.diagram_id}`);
  };

  return (
    <div className="p-8 text-center">
      {/* Success Icon */}
      <div className="mb-6 flex justify-center">
        <div className="rounded-full bg-green-100 p-6">
          <CheckCircle className="text-green-600" size={64} />
        </div>
      </div>

      {/* Success Message */}
      <h2 className="text-3xl font-bold mb-4 text-gray-900">Import Complete!</h2>
      <p className="text-gray-600 mb-8 text-lg">
        Your diagram has been successfully created with {importResult.nodes_imported} node
        {importResult.nodes_imported !== 1 ? 's' : ''} and {importResult.edges_imported} edge
        {importResult.edges_imported !== 1 ? 's' : ''}.
      </p>

      {/* Import Statistics */}
      <div className="max-w-md mx-auto mb-8 bg-gray-50 rounded-lg p-6 border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-4">Import Summary</h3>
        <div className="space-y-3 text-left">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Diagram ID:</span>
            <code className="text-sm bg-white px-2 py-1 rounded border border-gray-200 font-mono">
              {importResult.diagram_id}
            </code>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Nodes Imported:</span>
            <span className="font-semibold text-gray-900">{importResult.nodes_imported}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Edges Imported:</span>
            <span className="font-semibold text-gray-900">{importResult.edges_imported}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Status:</span>
            <span className="inline-flex items-center text-green-600 font-semibold">
              <CheckCircle size={16} className="mr-1" />
              Success
            </span>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {importResult.warnings && importResult.warnings.length > 0 && (
        <div className="max-w-2xl mx-auto mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-left">
          <div className="flex items-start">
            <AlertTriangle className="text-yellow-600 mr-3 mt-0.5 flex-shrink-0" size={20} />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">Import Warnings</h3>
              <p className="text-yellow-700 text-sm mb-2">
                The import completed successfully, but with the following warnings:
              </p>
              <ul className="list-disc list-inside space-y-1">
                {importResult.warnings.map((warning, idx) => (
                  <li key={idx} className="text-yellow-700 text-sm">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row justify-center gap-4 max-w-md mx-auto">
        <button
          onClick={handleViewDiagram}
          className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          <ExternalLink size={18} className="mr-2" />
          View Diagram
        </button>
        <button
          onClick={onReset}
          className="inline-flex items-center justify-center px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
        >
          <RefreshCw size={18} className="mr-2" />
          Import Another File
        </button>
      </div>

      {/* Additional Help */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Need help? Check out our{' '}
          <a href="/docs/import" className="text-blue-600 hover:text-blue-700 underline">
            import documentation
          </a>
          .
        </p>
      </div>
    </div>
  );
};

export default CompleteStep;