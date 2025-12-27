"""
Cypher Parser - Parse Cypher queries to extract graph patterns
"""
from typing import List, Dict, Any
import re


class CypherParser:
    """Parser for Cypher queries"""
    
    def parse(self, cypher: str) -> Dict[str, Any]:
        """
        Parse Cypher query and extract nodes and relationships
        
        Args:
            cypher: Cypher query string
            
        Returns:
            Dictionary with nodes and relationships
        """
        nodes = []
        relationships = []
        
        # Extract CREATE/MERGE statements
        create_pattern = r'(?:CREATE|MERGE)\s+(.+?)(?:RETURN|WHERE|WITH|$)'
        matches = re.finditer(create_pattern, cypher, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            pattern = match.group(1)
            
            # Extract nodes
            node_pattern = r'\((\w+):(\w+)(?:\s+\{(.+?)\})?\)'
            node_matches = re.finditer(node_pattern, pattern)
            
            for node_match in node_matches:
                var_name = node_match.group(1)
                label = node_match.group(2)
                properties = node_match.group(3)
                
                nodes.append({
                    "variable": var_name,
                    "label": label,
                    "properties": self._parse_properties(properties) if properties else {}
                })
            
            # Extract relationships
            rel_pattern = r'\((\w+)\)-\[:(\w+)(?:\s+\{(.+?)\})?\]->\((\w+)\)'
            rel_matches = re.finditer(rel_pattern, pattern)
            
            for rel_match in rel_matches:
                from_node = rel_match.group(1)
                rel_type = rel_match.group(2)
                properties = rel_match.group(3)
                to_node = rel_match.group(4)
                
                relationships.append({
                    "from": from_node,
                    "type": rel_type,
                    "to": to_node,
                    "properties": self._parse_properties(properties) if properties else {}
                })
        
        return {
            "nodes": nodes,
            "relationships": relationships
        }
    
    def _parse_properties(self, props_str: str) -> Dict[str, Any]:
        """Parse property string into dictionary"""
        properties = {}
        
        # Simple property parsing
        prop_pattern = r'(\w+):\s*(["\']?)(.+?)\2(?:,|$)'
        matches = re.finditer(prop_pattern, props_str)
        
        for match in matches:
            key = match.group(1)
            value = match.group(3)
            properties[key] = value
        
        return properties