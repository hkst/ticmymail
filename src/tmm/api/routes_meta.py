from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@router.get("/version", tags=["meta"])
async def version():
    return {"version": "0.1.0"}
