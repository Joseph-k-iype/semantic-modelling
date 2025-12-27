"""
XMI Parser - Parse XMI (XML Metadata Interchange) files
"""
from typing import Dict, Any, List
import xml.etree.ElementTree as ET


class XMIParser:
    """Parser for XMI files (UML interchange format)"""
    
    def parse(self, xmi_content: str) -> Dict[str, Any]:
        """
        Parse XMI content and extract UML model
        
        Args:
            xmi_content: XMI file content as string
            
        Returns:
            Dictionary with model elements
        """
        try:
            root = ET.fromstring(xmi_content)
        except ET.ParseError as e:
            return {
                "error": f"Failed to parse XMI: {str(e)}",
                "classes": [],
                "packages": [],
                "associations": []
            }
        
        classes = []
        packages = []
        associations = []
        
        # Extract UML classes
        for element in root.iter():
            if 'Class' in element.tag:
                classes.append(self._parse_class(element))
            elif 'Package' in element.tag:
                packages.append(self._parse_package(element))
            elif 'Association' in element.tag:
                associations.append(self._parse_association(element))
        
        return {
            "classes": classes,
            "packages": packages,
            "associations": associations
        }
    
    def _parse_class(self, element: ET.Element) -> Dict[str, Any]:
        """Parse UML class element"""
        return {
            "id": element.get('xmi.id', ''),
            "name": element.get('name', 'UnnamedClass'),
            "attributes": self._parse_attributes(element),
            "operations": self._parse_operations(element),
            "visibility": element.get('visibility', 'public')
        }
    
    def _parse_package(self, element: ET.Element) -> Dict[str, Any]:
        """Parse UML package element"""
        return {
            "id": element.get('xmi.id', ''),
            "name": element.get('name', 'UnnamedPackage'),
            "elements": []
        }
    
    def _parse_association(self, element: ET.Element) -> Dict[str, Any]:
        """Parse UML association element"""
        return {
            "id": element.get('xmi.id', ''),
            "name": element.get('name', ''),
            "ends": []
        }
    
    def _parse_attributes(self, class_element: ET.Element) -> List[Dict[str, Any]]:
        """Parse class attributes"""
        attributes = []
        for attr in class_element.iter():
            if 'Attribute' in attr.tag:
                attributes.append({
                    "name": attr.get('name', ''),
                    "type": attr.get('type', 'String'),
                    "visibility": attr.get('visibility', 'private')
                })
        return attributes
    
    def _parse_operations(self, class_element: ET.Element) -> List[Dict[str, Any]]:
        """Parse class operations/methods"""
        operations = []
        for op in class_element.iter():
            if 'Operation' in op.tag:
                operations.append({
                    "name": op.get('name', ''),
                    "returnType": op.get('returnType', 'void'),
                    "visibility": op.get('visibility', 'public')
                })
        return operations