from fastapi import FastAPI
from .routes_ingest import router as ingest_router
from .routes_email import router as email_router
from .routes_bigpanda import router as bigpanda_router
from .routes_meta import router as meta_router

app = FastAPI(
    title="ticmymail-part2",
    version="0.1.0",
    openapi_tags=[
        {"name": "ingest", "description": "Incident ingestion"},
        {"name": "email", "description": "Outbound email"},
        {"name": "bigpanda", "description": "BigPanda integration"},
        {"name": "meta", "description": "Health and version"},
    ],
)

app.include_router(ingest_router, prefix="/v1")
app.include_router(email_router, prefix="/v1")
app.include_router(bigpanda_router, prefix="/v1")
app.include_router(meta_router, prefix="/v1")
