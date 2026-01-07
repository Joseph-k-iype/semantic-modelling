// frontend/src/components/import/ProgressIndicator.tsx
/**
 * Progress indicator for import workflow steps
 */

import React from 'react';
import { Upload, Settings, Eye, CheckCircle } from 'lucide-react';
import { ImportStep } from '../../types/import';

interface ProgressIndicatorProps {
  currentStep: ImportStep;
}

interface StepInfo {
  id: ImportStep;
  label: string;
  icon: React.ReactNode;
  order: number;
}

const steps: StepInfo[] = [
  { id: 'upload', label: 'Upload', icon: <Upload size={18} />, order: 0 },
  { id: 'mapping', label: 'Mapping', icon: <Settings size={18} />, order: 1 },
  { id: 'preview', label: 'Preview', icon: <Eye size={18} />, order: 2 },
  { id: 'complete', label: 'Complete', icon: <CheckCircle size={18} />, order: 3 },
];

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStep }) => {
  const currentOrder = steps.find((s) => s.id === currentStep)?.order ?? 0;

  const getStepStatus = (stepOrder: number): 'complete' | 'current' | 'upcoming' => {
    if (stepOrder < currentOrder) return 'complete';
    if (stepOrder === currentOrder) return 'current';
    return 'upcoming';
  };

  const getStepClasses = (status: 'complete' | 'current' | 'upcoming'): string => {
    const baseClasses = 'flex items-center justify-center w-10 h-10 rounded-full transition-colors';

    switch (status) {
      case 'complete':
        return `${baseClasses} bg-green-500 text-white`;
      case 'current':
        return `${baseClasses} bg-blue-600 text-white ring-4 ring-blue-100`;
      case 'upcoming':
        return `${baseClasses} bg-gray-200 text-gray-600`;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const status = getStepStatus(step.order);

          return (
            <React.Fragment key={step.id}>
              {/* Step Circle */}
              <div className="flex flex-col items-center">
                <div className={getStepClasses(status)}>
                  {status === 'complete' ? (
                    <CheckCircle size={18} />
                  ) : (
                    step.icon
                  )}
                </div>
                <span
                  className={`mt-2 text-sm font-medium ${
                    status === 'current'
                      ? 'text-blue-600'
                      : status === 'complete'
                      ? 'text-green-600'
                      : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="flex-1 mx-4 h-1 relative">
                  <div className="absolute inset-0 bg-gray-200 rounded" />
                  <div
                    className={`absolute inset-0 rounded transition-all ${
                      step.order < currentOrder
                        ? 'bg-green-500 w-full'
                        : step.order === currentOrder
                        ? 'bg-blue-600 w-1/2'
                        : 'bg-gray-200 w-0'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default ProgressIndicator;