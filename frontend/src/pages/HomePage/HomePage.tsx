import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Package, Workflow, ArrowRight } from 'lucide-react';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Enterprise Modeling Platform
            </h1>
          </div>
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Sign In
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Professional Modeling Platform
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Create ER diagrams, UML models, and BPMN processes with our powerful, 
            web-based modeling tool. Open-source alternative to Visual Paradigm.
          </p>
          <button
            onClick={() => navigate('/diagram')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
          >
            Start Modeling
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-8 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-14 h-14 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Database className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">ER Diagrams</h3>
            <p className="text-gray-600 mb-4">
              Design database schemas with entities, attributes, and relationships. 
              Export to SQL DDL automatically.
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Entity-Relationship modeling</li>
              <li>• Primary & foreign keys</li>
              <li>• SQL export (PostgreSQL, MySQL)</li>
              <li>• Cardinality support</li>
            </ul>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-14 h-14 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Package className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">UML Diagrams</h3>
            <p className="text-gray-600 mb-4">
              Full UML 2.5 support with class, sequence, activity, and state diagrams.
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Class diagrams</li>
              <li>• Sequence diagrams</li>
              <li>• Activity diagrams</li>
              <li>• State machines</li>
            </ul>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-14 h-14 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Workflow className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">BPMN 2.0</h3>
            <p className="text-gray-600 mb-4">
              Model business processes with full BPMN 2.0 support including swimlanes.
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Tasks & events</li>
              <li>• Gateways & flows</li>
              <li>• Pools & lanes</li>
              <li>• Process validation</li>
            </ul>
          </div>
        </div>

        {/* Additional Features */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Enterprise Features
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🎨</div>
              <div className="font-semibold text-gray-900">Interactive UI</div>
              <div className="text-sm text-gray-600">Drag & drop</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">✅</div>
              <div className="font-semibold text-gray-900">Validation</div>
              <div className="text-sm text-gray-600">Real-time rules</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">📤</div>
              <div className="font-semibold text-gray-900">Export</div>
              <div className="text-sm text-gray-600">SQL, Cypher, SVG</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">⚡</div>
              <div className="font-semibold text-gray-900">Auto-Layout</div>
              <div className="text-sm text-gray-600">Smart positioning</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            © 2024 Enterprise Modeling Platform. Open Source - MIT License
          </p>
        </div>
      </footer>
    </div>
  );
};