// frontend/src/components/import/UploadStep.tsx
/**
 * File upload step component
 */

import React, { useState, useCallback } from 'react';
import { Upload, FileText, Download, Table, Code } from 'lucide-react';
import importApiClient from '../../services/importApiClient';
import { isValidFileType } from '../../utils/importUtils';

interface UploadStepProps {
  onFileUpload: (file: File) => Promise<void>;
  loading: boolean;
  uploadProgress: number;
}

const UploadStep: React.FC<UploadStepProps> = ({ onFileUpload, loading, uploadProgress }) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        if (isValidFileType(file.name)) {
          onFileUpload(file);
        } else {
          alert('Invalid file type. Please upload CSV, Excel, or JSON files.');
        }
      }
    },
    [onFileUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        if (isValidFileType(file.name)) {
          onFileUpload(file);
        } else {
          alert('Invalid file type. Please upload CSV, Excel, or JSON files.');
        }
      }
    },
    [onFileUpload]
  );

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Upload Your Data File</h2>

      {/* File Upload Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 bg-white'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {loading ? (
          <div className="space-y-4">
            <Upload className="mx-auto text-blue-600 animate-bounce" size={48} />
            <p className="text-xl font-medium text-gray-700">Uploading...</p>
            <div className="w-64 mx-auto bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500">{uploadProgress}%</p>
          </div>
        ) : (
          <>
            <Upload className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-xl font-medium text-gray-700 mb-2">
              Drag and drop your file here
            </p>
            <p className="text-gray-500 mb-6">or</p>
            <label className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
              <input
                type="file"
                className="hidden"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleChange}
                disabled={loading}
              />
              Choose File
            </label>
            <p className="text-sm text-gray-500 mt-4">
              Supported formats: CSV, Excel (.xlsx, .xls), JSON (max 10MB)
            </p>
          </>
        )}
      </div>

      {/* Template Download */}
      <div className="mt-8 p-6 bg-blue-50 rounded-lg">
        <div className="flex items-start">
          <FileText className="text-blue-600 mr-3 mt-1 flex-shrink-0" size={24} />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900 mb-2">Need a Template?</h3>
            <p className="text-blue-700 mb-4 text-sm">
              Download our template files to see the expected structure for importing UML diagrams.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => importApiClient.downloadJsonTemplate()}
                className="inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm"
              >
                <Download size={16} className="mr-2" />
                JSON Template
              </button>
              <button
                onClick={() => importApiClient.downloadCsvTemplate()}
                className="inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm"
              >
                <Download size={16} className="mr-2" />
                CSV Template
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Format Guide */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">Supported Formats</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FormatCard
            icon={<Table size={24} />}
            title="CSV Format"
            description="One node per row with columns for ID, type, label, attributes, and methods"
            example={`id,type,label,attributes
user,class,User,"id:UUID;name:String"`}
          />
          <FormatCard
            icon={<FileText size={24} />}
            title="Excel Format"
            description="Separate sheets for Nodes and Edges with column headers"
            example="Sheet: Nodes
Columns: id, type, label, attributes"
          />
          <FormatCard
            icon={<Code size={24} />}
            title="JSON Format"
            description="Direct template format with nodes and edges arrays"
            example='{"nodes": [...], "edges": [...]}'
          />
        </div>
      </div>
    </div>
  );
};

// Format Card Component
interface FormatCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  example: string;
}

const FormatCard: React.FC<FormatCardProps> = ({ icon, title, description, example }) => (
  <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
    <div className="text-blue-600 mb-3">{icon}</div>
    <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
    <p className="text-sm text-gray-600 mb-3">{description}</p>
    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto border border-gray-200">
      {example}
    </pre>
  </div>
);

export default UploadStep;