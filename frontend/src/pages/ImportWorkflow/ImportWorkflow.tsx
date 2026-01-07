// frontend/src/pages/ImportWorkflow/ImportWorkflow.tsx
/**
 * Main Import Workflow Page
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';
import { useImportWorkflow } from '../../hooks/useImportWorkflow';
import UploadStep from '../../components/import/UploadStep';
import MappingStep from '../../components/import/MappingStep';
import PreviewStep from '../../components/import/PreviewStep';
import CompleteStep from '../../components/import/CompleteStep';
import ProgressIndicator from '../../components/import/ProgressIndicator';

const ImportWorkflow: React.FC = () => {
  const workflow = useImportWorkflow();

  const renderStep = () => {
    switch (workflow.step) {
      case 'upload':
        return (
          <UploadStep
            onFileUpload={workflow.uploadFile}
            loading={workflow.loading}
            uploadProgress={workflow.uploadProgress}
          />
        );

      case 'mapping':
        return workflow.filePreview ? (
          <MappingStep
            filePreview={workflow.filePreview}
            fileId={workflow.fileId}
            onGeneratePreview={workflow.generatePreview}
            loading={workflow.loading}
            onBack={() => workflow.goToStep('upload')}
          />
        ) : null;

      case 'preview':
        return workflow.previewData ? (
          <PreviewStep
            previewData={workflow.previewData}
            onExecute={workflow.executeImport}
            onBack={() => workflow.goToStep('mapping')}
            loading={workflow.loading}
          />
        ) : null;

      case 'complete':
        return workflow.importResult ? (
          <CompleteStep importResult={workflow.importResult} onReset={workflow.reset} />
        ) : null;

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Import Wizard</h1>
          <p className="text-gray-600">
            Import UML diagrams from CSV, Excel, or JSON files
          </p>
        </div>

        {/* Progress Indicator */}
        <ProgressIndicator currentStep={workflow.step} />

        {/* Error Display */}
        {workflow.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="text-red-600 mr-3 mt-0.5 flex-shrink-0" size={20} />
            <div className="flex-1">
              <p className="font-medium text-red-900">Error</p>
              <p className="text-red-700 text-sm mt-1">{workflow.error}</p>
            </div>
            <button
              onClick={workflow.clearError}
              className="text-red-600 hover:text-red-800 ml-4"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm">
          {renderStep()}
        </div>
      </div>
    </div>
  );
};

export default ImportWorkflow;