// frontend/src/pages/HomePage/HomePage.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Enterprise Modeling Platform
          </h1>
          <p className="text-xl text-gray-600">
            Create, manage, and collaborate on enterprise models
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              ER Modeling
            </h3>
            <p className="text-gray-600 mb-4">
              Design database schemas and relationships
            </p>
            <button
              onClick={() => navigate('/workspace/new')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Get Started →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              UML Diagrams
            </h3>
            <p className="text-gray-600 mb-4">
              Create comprehensive UML diagrams
            </p>
            <button
              onClick={() => navigate('/workspace/new')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Get Started →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              BPMN Process
            </h3>
            <p className="text-gray-600 mb-4">
              Model business processes and workflows
            </p>
            <button
              onClick={() => navigate('/workspace/new')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Get Started →
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Recent Workspaces
          </h2>
          <p className="text-gray-600">
            Your recent workspaces will appear here
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;