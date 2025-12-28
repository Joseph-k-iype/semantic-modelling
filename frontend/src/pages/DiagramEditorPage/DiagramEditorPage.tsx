// frontend/src/pages/DiagramEditorPage/DiagramEditorPage.tsx

import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DiagramCanvas from '../../components/diagram/DiagramCanvas/DiagramCanvas';
import { ArrowLeft, Save, Download, Share2, History, Layout } from 'lucide-react';

export const DiagramEditorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [modelId, setModelId] = useState<string>('');
  const [diagramId, setDiagramId] = useState<string>('');
  const [diagramName, setDiagramName] = useState<string>('');
  const [notation, setNotation] = useState<'er' | 'uml-class' | 'uml-sequence' | 'bpmn' | 'uml-interaction'>('uml-class');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Get parameters from URL
    const id = searchParams.get('id') || '';
    const model = searchParams.get('model') || '';
    const type = searchParams.get('type') || 'UML_CLASS';
    const name = searchParams.get('name') || 'Untitled Diagram';
    
    setDiagramId(id);
    setModelId(model);
    setDiagramName(name);
    
    // Map string to notation type
    let notationType: 'er' | 'uml-class' | 'uml-sequence' | 'bpmn' | 'uml-interaction' = 'uml-class';
    
    switch (type.toUpperCase()) {
      case 'ER':
        notationType = 'er';
        break;
      case 'UML_CLASS':
        notationType = 'uml-class';
        break;
      case 'UML_SEQUENCE':
        notationType = 'uml-sequence';
        break;
      case 'UML_INTERACTION':
        notationType = 'uml-interaction';
        break;
      case 'BPMN':
        notationType = 'bpmn';
        break;
      default:
        notationType = 'uml-class';
    }
    
    setNotation(notationType);
    setIsLoading(false);
  }, [searchParams]);

  const handleBack = () => {
    navigate(-1);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save logic will be implemented here
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulated delay
      console.log('Diagram saved successfully');
    } catch (error) {
      console.error('Failed to save diagram:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = () => {
    console.log('Export diagram');
    // Export logic will be implemented
  };

  const handleShare = () => {
    console.log('Share diagram');
    // Share logic will be implemented
  };

  const handleVersionHistory = () => {
    console.log('View version history');
    // Version history logic will be implemented
  };

  const handleAutoLayout = () => {
    console.log('Auto layout');
    // Auto layout logic will be implemented
  };

  if (isLoading) {
    return (
      <div style={{
        width: '100%',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f9fafb'
      }}>
        <div style={{
          textAlign: 'center'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #e5e7eb',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{
            color: '#6b7280',
            fontSize: '14px'
          }}>
            Loading diagram...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      width: '100%',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#f9fafb'
    }}>
      {/* Toolbar */}
      <div style={{
        height: '60px',
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: '12px',
        flexShrink: 0
      }}>
        {/* Back Button */}
        <button
          onClick={handleBack}
          style={{
            padding: '8px 12px',
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
          }}
        >
          <ArrowLeft size={16} />
          Back
        </button>

        {/* Diagram Name */}
        <div style={{
          flex: 1,
          fontSize: '16px',
          fontWeight: '600',
          color: '#111827'
        }}>
          {diagramName}
        </div>

        {/* Action Buttons */}
        <button
          onClick={handleAutoLayout}
          style={{
            padding: '8px 12px',
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
          }}
        >
          <Layout size={16} />
          Auto Layout
        </button>

        <button
          onClick={handleVersionHistory}
          style={{
            padding: '8px 12px',
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
          }}
        >
          <History size={16} />
          History
        </button>

        <button
          onClick={handleExport}
          style={{
            padding: '8px 12px',
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
          }}
        >
          <Download size={16} />
          Export
        </button>

        <button
          onClick={handleShare}
          style={{
            padding: '8px 12px',
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
          }}
        >
          <Share2 size={16} />
          Share
        </button>

        <button
          onClick={handleSave}
          disabled={isSaving}
          style={{
            padding: '8px 16px',
            background: '#3b82f6',
            border: 'none',
            borderRadius: '6px',
            cursor: isSaving ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            color: 'white',
            fontWeight: '500',
            transition: 'all 0.2s',
            opacity: isSaving ? 0.7 : 1
          }}
          onMouseEnter={(e) => {
            if (!isSaving) {
              e.currentTarget.style.background = '#2563eb';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#3b82f6';
          }}
        >
          <Save size={16} />
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>

      {/* Canvas Area */}
      <div style={{
        flex: 1,
        overflow: 'hidden',
        position: 'relative'
      }}>
        {modelId && diagramId ? (
          <DiagramCanvas
            modelId={modelId}
            diagramId={diagramId}
            notation={notation}
          />
        ) : (
          <div style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <p style={{
              color: '#9ca3af',
              fontSize: '14px'
            }}>
              Invalid diagram parameters
            </p>
          </div>
        )}
      </div>

      {/* Add spinner animation */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default DiagramEditorPage;