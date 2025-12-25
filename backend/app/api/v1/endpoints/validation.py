from fastapi import APIRouter

router = APIRouter()

@router.post("/validate")
async def validate_model():
    return {"valid": True, "errors": []}
