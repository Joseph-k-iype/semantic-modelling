// frontend/src/pages/DiagramEditorPage/DiagramEditorPage.tsx
// FIXED: Auto-create diagram when navigating to /diagram/new
// Path: frontend/src/pages/DiagramEditorPage/DiagramEditorPage.tsx

import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DiagramCanvas from '../../components/diagram/DiagramCanvas/DiagramCanvas';
import { ArrowLeft, Save, Download, Share2, History, Layout } from 'lucide-react';
import { apiClient } from '../../services/api/client';

export const DiagramEditorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [modelId, setModelId] = useState<string>('');
  const [diagramId, setDiagramId] = useState<string>('');
  const [diagramName, setDiagramName] = useState<string>('');
  const [notation, setNotation] = useState<'er' | 'uml-class' | 'uml-sequence' | 'bpmn' | 'uml-interaction'>('uml-class');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const initializeDiagram = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // Get parameters from URL
        const id = searchParams.get('id') || '';
        const model = searchParams.get('model') || '';
        const type = searchParams.get('type') || 'UML_CLASS';
        const name = searchParams.get('name') || 'Untitled Diagram';
        
        // Map diagram type string to notation type
        let notationType: 'er' | 'uml-class' | 'uml-sequence' | 'bpmn' | 'uml-interaction' = 'uml-class';
        let notationTypeBackend = 'UML_CLASS'; // Backend expects uppercase with underscore
        
        switch (type.toUpperCase()) {
          case 'ER':
            notationType = 'er';
            notationTypeBackend = 'ER';
            break;
          case 'UML_CLASS':
          case 'UML-CLASS':
            notationType = 'uml-class';
            notationTypeBackend = 'UML_CLASS';
            break;
          case 'UML_SEQUENCE':
          case 'UML-SEQUENCE':
            notationType = 'uml-sequence';
            notationTypeBackend = 'UML_SEQUENCE';
            break;
          case 'UML_INTERACTION':
          case 'UML-INTERACTION':
            notationType = 'uml-interaction';
            notationTypeBackend = 'UML_INTERACTION';
            break;
          case 'BPMN':
            notationType = 'bpmn';
            notationTypeBackend = 'BPMN';
            break;
          default:
            notationType = 'uml-class';
            notationTypeBackend = 'UML_CLASS';
        }
        
        setNotation(notationType);
        setDiagramName(name);
        
        // If we have both IDs, we're editing an existing diagram
        if (id && model) {
          setDiagramId(id);
          setModelId(model);
          setIsLoading(false);
        }
        // If we don't have IDs, we're creating a new diagram
        else {
          console.log('Creating new diagram:', { name, type: notationTypeBackend });
          
          // Create new diagram via API
          const response = await apiClient.post('/diagrams/', {
            name: name,
            notation_type: notationTypeBackend,
            model_id: model || null,  // Optional - backend will create model if null
            model_name: model ? null : `Model for ${name}`
          });
          
          const newDiagram = response.data;
          console.log('Diagram created:', newDiagram);
          
          // Set the IDs from the created diagram
          setDiagramId(newDiagram.id);
          setModelId(newDiagram.model_id);
          
          // Update URL to include IDs (so refresh works)
          const newUrl = `/diagram/new?id=${newDiagram.id}&model=${newDiagram.model_id}&type=${type}&name=${encodeURIComponent(name)}`;
          window.history.replaceState({}, '', newUrl);
          
          setIsLoading(false);
        }
      } catch (err: any) {
        console.error('Error initializing diagram:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to initialize diagram');
        setIsLoading(false);
      }
    };
    
    initializeDiagram();
  }, [searchParams]);

  const handleBack = () => {
    navigate(-1);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement actual save logic via DiagramCanvas
      console.log('Saving diagram:', diagramId);
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate save
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f9fafb'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid #e5e7eb',
            borderTop: '3px solid #3b82f6',
            borderRadius: '50%',
            margin: '0 auto 16px',
            animation: 'spin 1s linear infinite'
          }} />
          <p style={{
            color: '#6b7280',
            fontSize: '14px'
          }}>
            {diagramId ? 'Loading diagram...' : 'Creating diagram...'}
          </p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f9fafb'
      }}>
        <div style={{
          maxWidth: '400px',
          padding: '24px',
          background: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: '#fee2e2',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '8px'
          }}>
            Failed to Create Diagram
          </h3>
          <p style={{
            color: '#6b7280',
            fontSize: '14px',
            marginBottom: '24px'
          }}>
            {error}
          </p>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Go Back Home
          </button>
        </div>
      </div>
    );
  }

  // Show diagram editor
  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#ffffff'
    }}>
      {/* Header */}
      <div style={{
        height: '60px',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        background: 'white'
      }}>
        {/* Left side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleBack}
            style={{
              padding: '8px',
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6b7280'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f3f4f6';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <ArrowLeft size={20} />
          </button>
          
          <div>
            <h1 style={{
              fontSize: '16px',
              fontWeight: '600',
              color: '#111827',
              margin: 0
            }}>
              {diagramName}
            </h1>
            <p style={{
              fontSize: '12px',
              color: '#6b7280',
              margin: 0
            }}>
              {notation.toUpperCase().replace('-', ' ')} Diagram
            </p>
          </div>
        </div>

        {/* Right side - Action buttons */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            style={{
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f9fafb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <Layout size={16} />
            Layout
          </button>
          
          <button
            style={{
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f9fafb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <History size={16} />
            History
          </button>
          
          <button
            style={{
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f9fafb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <Share2 size={16} />
            Share
          </button>
          
          <button
            style={{
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f9fafb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <Download size={16} />
            Export
          </button>
          
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: 'white',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
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
              Initializing diagram...
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