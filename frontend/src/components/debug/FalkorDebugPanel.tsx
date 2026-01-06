// frontend/src/components/debug/FalkorDebugPanel.tsx
/**
 * FalkorDB Debug Panel - Test FalkorDB Sync
 * Add this to OntologyBuilderPage to debug sync issues
 */

import React, { useState } from 'react';
import { Database, RefreshCw, Search } from 'lucide-react';
import apiClient from '../../services/api/client'

interface FalkorDebugPanelProps {
  diagramId: string;
  graphName: string;
}

export const FalkorDebugPanel: React.FC<FalkorDebugPanelProps> = ({ 
  diagramId, 
  graphName 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get(`/diagrams/${diagramId}/falkor-stats`);
      setStats(response.data);
      
    } catch (err: any) {
      console.error('Failed to fetch FalkorDB stats:', err);
      setError(err.response?.data?.detail || 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  };

  const forceSync = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post(`/diagrams/${diagramId}/force-sync`);
      console.log('Force sync result:', response.data);
      
      // Refresh stats after sync
      await fetchStats();
      
      alert('Sync completed successfully!');
      
    } catch (err: any) {
      console.error('Force sync failed:', err);
      setError(err.response?.data?.detail || 'Force sync failed');
      alert('Sync failed: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const testQuery = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post(`/diagrams/${diagramId}/falkor-query`, {
        query: "MATCH (n:Concept) RETURN n.id, n.label, n.node_type, labels(n) LIMIT 10"
      });
      
      console.log('Query result:', response.data);
      alert('Query executed - check console for results');
      
    } catch (err: any) {
      console.error('Query failed:', err);
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          fetchStats();
        }}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700"
        title="Open FalkorDB Debug Panel"
      >
        <Database size={24} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white shadow-2xl rounded-lg border-2 border-gray-300 w-96 max-h-[600px] overflow-auto">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 flex justify-between items-center rounded-t-lg">
        <div className="flex items-center gap-2">
          <Database size={20} />
          <h3 className="font-bold">FalkorDB Debug</h3>
        </div>
        <button 
          onClick={() => setIsOpen(false)}
          className="text-white hover:bg-blue-700 rounded px-2 py-1"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Graph Info */}
        <div className="bg-gray-50 p-3 rounded border">
          <h4 className="font-semibold text-sm mb-2">Graph Name:</h4>
          <code className="text-xs bg-gray-200 px-2 py-1 rounded block">
            {graphName || 'Not set'}
          </code>
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <button
            onClick={fetchStats}
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 px-4 rounded flex items-center justify-center gap-2 hover:bg-green-700 disabled:opacity-50"
          >
            <Search size={16} />
            Fetch Stats
          </button>

          <button
            onClick={forceSync}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded flex items-center justify-center gap-2 hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw size={16} />
            Force Sync
          </button>

          <button
            onClick={testQuery}
            disabled={loading}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded flex items-center justify-center gap-2 hover:bg-purple-700 disabled:opacity-50"
          >
            <Search size={16} />
            Test Query
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center text-gray-600">
            Loading...
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 p-3 rounded text-sm">
            {error}
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">FalkorDB Statistics:</h4>
            
            {stats.falkordb_stats?.success ? (
              <div className="bg-green-50 border border-green-300 p-3 rounded space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium">Total Nodes:</span>
                  <span className="font-bold text-green-700">
                    {stats.falkordb_stats.total_nodes}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Total Edges:</span>
                  <span className="font-bold text-green-700">
                    {stats.falkordb_stats.total_edges}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Containment:</span>
                  <span className="font-bold text-green-700">
                    {stats.falkordb_stats.total_contains}
                  </span>
                </div>

                {stats.falkordb_stats.node_types && (
                  <div className="mt-3 pt-3 border-t border-green-200">
                    <div className="font-medium mb-2">Node Types:</div>
                    {Object.entries(stats.falkordb_stats.node_types).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-xs">
                        <span className="capitalize">{type}:</span>
                        <span className="font-mono">{count as number}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-yellow-50 border border-yellow-300 text-yellow-700 p-3 rounded text-sm">
                {stats.falkordb_stats?.error || 'FalkorDB not available'}
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-300 p-3 rounded text-xs">
          <p className="font-semibold mb-1">How to use:</p>
          <ol className="list-decimal list-inside space-y-1 text-gray-700">
            <li>Click "Fetch Stats" to see current graph data</li>
            <li>Click "Force Sync" to re-sync diagram to FalkorDB</li>
            <li>Click "Test Query" to run a sample Cypher query</li>
            <li>Check browser console for detailed logs</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default FalkorDebugPanel;