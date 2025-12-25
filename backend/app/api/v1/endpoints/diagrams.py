from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_diagrams():
    return {"diagrams": []}

@router.post("/")
async def create_diagram():
    return {"message": "Diagram creation not yet implemented"}