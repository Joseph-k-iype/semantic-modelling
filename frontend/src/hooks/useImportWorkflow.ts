// frontend/src/hooks/useImportWorkflow.ts
/**
 * Custom hook for managing import workflow state
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import importApiClient from '../services/importApiClient';
import {
  ImportStep,
  FileUploadResponse,
  ImportMappingConfig,
  ImportPreviewResponse,
  ImportExecutionResponse,
} from '../types/import';

interface UseImportWorkflowReturn {
  // State
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

  // Actions
  uploadFile: (file: File) => Promise<void>;
  generatePreview: (config: ImportMappingConfig) => Promise<void>;
  executeImport: () => Promise<void>;
  goToStep: (step: ImportStep) => void;
  reset: () => void;
  clearError: () => void;
}

export const useImportWorkflow = (): UseImportWorkflowReturn => {
  const navigate = useNavigate();

  // State
  const [step, setStep] = useState<ImportStep>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string>('');
  const [filePreview, setFilePreview] = useState<FileUploadResponse | null>(null);
  const [mappingConfig, setMappingConfig] = useState<ImportMappingConfig | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [importResult, setImportResult] = useState<ImportExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Upload file
   */
  const uploadFile = useCallback(async (uploadedFile: File) => {
    setLoading(true);
    setError('');
    setUploadProgress(0);

    try {
      const response = await importApiClient.uploadFile(uploadedFile, (progress) => {
        setUploadProgress(progress);
      });

      setFile(uploadedFile);
      setFileId(response.file_id);
      setFilePreview(response);
      setStep('mapping');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  }, []);

  /**
   * Generate preview
   */
  const generatePreview = useCallback(async (config: ImportMappingConfig) => {
    setLoading(true);
    setError('');

    try {
      // Validate config first
      const validationErrors = importApiClient.validateMappingConfig(config);
      if (validationErrors.length > 0) {
        throw new Error(validationErrors.join('; '));
      }

      const response = await importApiClient.generatePreview(config);
      setMappingConfig(config);
      setPreviewData(response);
      setStep('preview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview generation failed');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Execute import
   */
  const executeImport = useCallback(async () => {
    if (!mappingConfig) {
      setError('Mapping configuration is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await importApiClient.executeImport(mappingConfig);
      setImportResult(response);
      setStep('complete');

      // Cleanup temp file
      if (fileId) {
        try {
          await importApiClient.deleteTempFile(fileId);
        } catch (cleanupError) {
          console.warn('Failed to cleanup temp file:', cleanupError);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import execution failed');
    } finally {
      setLoading(false);
    }
  }, [mappingConfig, fileId]);

  /**
   * Navigate to specific step
   */
  const goToStep = useCallback((newStep: ImportStep) => {
    setStep(newStep);
    setError('');
  }, []);

  /**
   * Reset workflow
   */
  const reset = useCallback(() => {
    // Cleanup temp file if exists
    if (fileId) {
      importApiClient.deleteTempFile(fileId).catch(console.warn);
    }

    setStep('upload');
    setFile(null);
    setFileId('');
    setFilePreview(null);
    setMappingConfig(null);
    setPreviewData(null);
    setImportResult(null);
    setLoading(false);
    setError('');
    setUploadProgress(0);
  }, [fileId]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError('');
  }, []);

  return {
    // State
    step,
    file,
    fileId,
    filePreview,
    mappingConfig,
    previewData,
    importResult,
    loading,
    error,
    uploadProgress,

    // Actions
    uploadFile,
    generatePreview,
    executeImport,
    goToStep,
    reset,
    clearError,
  };
};

export default useImportWorkflow;