# backend/app/api/v1/endpoints/import_data.py
"""
Data Import API Endpoints
Handles file upload, mapping configuration, preview, and execution
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import uuid
from pathlib import Path
import tempfile
import json

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.import_template import (
    FileUploadResponse,
    ImportMappingConfig,
    ImportPreviewResponse,
    ImportExecutionResponse,
    ImportTemplate,
)
from app.services.import_service import ImportService

logger = structlog.get_logger()

router = APIRouter()


def get_import_service(db: AsyncSession = Depends(get_db)) -> ImportService:
    """Dependency for import service"""
    return ImportService(db)


@router.get("/template")
async def get_import_template() -> Dict[str, Any]:
    """
    Get the import template structure with examples
    Helps users understand the expected format
    """
    return {
        "description": "Template for importing UML diagrams",
        "supported_node_types": ["package", "class", "object", "interface", "enumeration"],
        "supported_edge_types": ["association", "aggregation", "composition", "generalization", "realization", "dependency"],
        "template_structure": {
            "nodes": [
                {
                    "id": "unique_identifier",
                    "type": "class|interface|object|package|enumeration",
                    "label": "Display Name",
                    "attributes": [{"name": "attr_name", "type": "String", "visibility": "+"}],
                    "methods": [{"name": "method_name", "return_type": "void", "visibility": "+"}],
                    "literals": [{"name": "ENUM_VALUE", "value": "1"}]
                }
            ],
            "edges": [
                {
                    "source": "node_id_1",
                    "target": "node_id_2",
                    "type": "association|aggregation|composition|etc",
                    "label": "relationship_name",
                    "source_multiplicity": "1",
                    "target_multiplicity": "0..*"
                }
            ]
        },
        "examples": {
            "csv_structure": {
                "description": "CSV with one node per row",
                "columns": ["id", "type", "label", "attributes", "methods", "description"],
                "example_row": {
                    "id": "user_class",
                    "type": "class",
                    "label": "User",
                    "attributes": "id:UUID;username:String;email:String",
                    "methods": "login(password:String):boolean;logout():void",
                    "description": "User entity"
                }
            },
            "excel_structure": {
                "description": "Excel with separate sheets for nodes and edges",
                "sheets": {
                    "Nodes": "Contains node definitions",
                    "Edges": "Contains relationship definitions"
                }
            },
            "json_structure": {
                "description": "Direct JSON following the template structure",
                "format": "Match the ImportTemplate schema exactly"
            }
        }
    }


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    *,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service)
) -> Any:
    """
    Upload a file for import (CSV, Excel, or JSON)
    Returns file preview and detected structure
    """
    try:
        # Validate file type
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in ['.csv', '.xlsx', '.xls', '.json']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Supported: .csv, .xlsx, .xls, .json"
            )
        
        logger.info(
            "file_upload_started",
            filename=filename,
            user_id=str(current_user.id)
        )
        
        # Read file content
        content = await file.read()
        
        # Process file and generate preview
        result = await import_service.process_uploaded_file(
            filename=filename,
            content=content,
            user_id=str(current_user.id)
        )
        
        logger.info(
            "file_upload_complete",
            file_id=result["file_id"],
            file_type=result["file_type"]
        )
        
        return FileUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_upload_failed", error=str(e), filename=filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    *,
    mapping_config: ImportMappingConfig,
    current_user: User = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service)
) -> Any:
    """
    Preview import based on mapping configuration
    Shows what will be created without actually creating it
    """
    try:
        logger.info(
            "import_preview_started",
            file_id=mapping_config.file_id,
            user_id=str(current_user.id)
        )
        
        # Generate preview
        preview = await import_service.preview_import(
            mapping_config=mapping_config,
            user_id=str(current_user.id)
        )
        
        logger.info(
            "import_preview_complete",
            total_nodes=preview.total_nodes,
            total_edges=preview.total_edges
        )
        
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("import_preview_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview import: {str(e)}"
        )


@router.post("/execute", response_model=ImportExecutionResponse)
async def execute_import(
    *,
    mapping_config: ImportMappingConfig,
    current_user: User = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service)
) -> Any:
    """
    Execute the import and create the diagram
    Creates nodes, edges, and syncs to FalkorDB
    """
    try:
        logger.info(
            "import_execution_started",
            file_id=mapping_config.file_id,
            diagram_name=mapping_config.diagram_name,
            user_id=str(current_user.id)
        )
        
        # Execute import
        result = await import_service.execute_import(
            mapping_config=mapping_config,
            user_id=str(current_user.id),
            username=current_user.username or current_user.email.split('@')[0]
        )
        
        logger.info(
            "import_execution_complete",
            diagram_id=result.diagram_id,
            nodes_imported=result.nodes_imported,
            edges_imported=result.edges_imported
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("import_execution_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute import: {str(e)}"
        )


@router.post("/direct", response_model=ImportExecutionResponse)
async def direct_import(
    *,
    db: AsyncSession = Depends(get_db),
    template_data: ImportTemplate,
    diagram_name: str,
    workspace_name: str,
    current_user: User = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service)
) -> Any:
    """
    Direct import from JSON template (skip file upload and mapping)
    For users who already have data in the correct format
    """
    try:
        logger.info(
            "direct_import_started",
            diagram_name=diagram_name,
            workspace_name=workspace_name,
            user_id=str(current_user.id)
        )
        
        username = current_user.username or current_user.email.split('@')[0]
        
        # Execute direct import
        result = await import_service.direct_import(
            template_data=template_data,
            diagram_name=diagram_name,
            workspace_name=workspace_name,
            user_id=str(current_user.id),
            username=username
        )
        
        logger.info(
            "direct_import_complete",
            diagram_id=result.diagram_id,
            nodes_imported=result.nodes_imported
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("direct_import_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute direct import: {str(e)}"
        )


@router.delete("/file/{file_id}")
async def delete_temp_file(
    *,
    file_id: str,
    current_user: User = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service)
) -> Dict[str, Any]:
    """
    Delete temporary uploaded file
    """
    try:
        await import_service.delete_temp_file(file_id, str(current_user.id))
        return {"success": True, "message": "File deleted"}
    except Exception as e:
        logger.error("file_deletion_failed", error=str(e), file_id=file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/examples")
async def get_import_examples() -> Dict[str, Any]:
    """
    Get example files and mappings for different scenarios
    """
    return {
        "csv_examples": {
            "simple_classes": {
                "description": "Simple class diagram with attributes",
                "csv_content": """id,type,label,attributes
user,class,User,"id:UUID;username:String;email:String"
account,class,Account,"id:UUID;balance:Decimal;type:String"
transaction,class,Transaction,"id:UUID;amount:Decimal;date:Date" """,
                "edges_csv": """source,target,type,label,source_multiplicity,target_multiplicity
user,account,association,owns,1,1..*
account,transaction,composition,contains,1,0..*"""
            },
            "with_methods": {
                "description": "Classes with methods",
                "csv_content": """id,type,label,attributes,methods
user,class,User,"id:UUID;username:String","login(password:String):boolean;logout():void"
auth_service,class,AuthService,"sessions:Map","authenticate(user:User,password:String):Token" """
            }
        },
        "json_example": {
            "description": "Complete JSON template example",
            "content": {
                "nodes": [
                    {
                        "id": "payment_package",
                        "type": "package",
                        "label": "Payment System"
                    },
                    {
                        "id": "payment_class",
                        "type": "class",
                        "label": "Payment",
                        "parent_package_id": "payment_package",
                        "attributes": [
                            {"name": "amount", "type": "Decimal", "visibility": "-"},
                            {"name": "currency", "type": "String", "visibility": "-"}
                        ],
                        "methods": [
                            {
                                "name": "process",
                                "return_type": "boolean",
                                "visibility": "+",
                                "parameters": []
                            }
                        ]
                    }
                ],
                "edges": [
                    {
                        "source": "user",
                        "target": "payment_class",
                        "type": "association",
                        "label": "makes",
                        "source_multiplicity": "1",
                        "target_multiplicity": "0..*"
                    }
                ]
            }
        }
    }