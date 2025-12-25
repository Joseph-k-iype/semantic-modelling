from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_models():
    return {"models": []}

@router.post("/")
async def create_model():
    return {"message": "Model creation not yet implemented"}
