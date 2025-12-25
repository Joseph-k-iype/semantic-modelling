from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_workspaces():
    return {"workspaces": []}

@router.post("/")
async def create_workspace():
    return {"message": "Workspace creation not yet implemented"}