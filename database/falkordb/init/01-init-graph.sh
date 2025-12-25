#!/bin/bash
# database/falkordb/init/01-init-graph.sh
# Initialize FalkorDB graph database

echo "================================================"
echo "Initializing FalkorDB Graph Database"
echo "================================================"

# Wait for FalkorDB to be ready
until redis-cli -p 6379 PING > /dev/null 2>&1; do
    echo "Waiting for FalkorDB to be ready..."
    sleep 1
done

echo "FalkorDB is ready!"

# Create the modeling graph
redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE (n:InitNode {name: 'initialization', created_at: timestamp()})" > /dev/null 2>&1
redis-cli -p 6379 GRAPH.QUERY modeling_graph "MATCH (n:InitNode) DELETE n" > /dev/null 2>&1

echo "Graph 'modeling_graph' initialized successfully"

# Create indexes for better performance
redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE INDEX ON :Concept(id)" > /dev/null 2>&1
redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE INDEX ON :Concept(name)" > /dev/null 2>&1
redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE INDEX ON :Attribute(id)" > /dev/null 2>&1
redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE INDEX ON :Relationship(id)" > /dev/null 2>&1

echo "Indexes created successfully"

echo "================================================"
echo "FalkorDB initialization complete!"
echo "================================================"
echo "Graph: modeling_graph"
echo "Access FalkorDB Browser at: http://localhost:3000"
echo "================================================"