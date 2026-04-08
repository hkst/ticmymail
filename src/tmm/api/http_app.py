from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .routes_ingest import router as ingest_router
from .routes_email import router as email_router
from .routes_bigpanda import router as bigpanda_router
from .routes_servicenow import router as servicenow_router
from .routes_jira import router as jira_router
from .routes_meta import router as meta_router
from tmm.logger import log_error
from tmm.service.errors import AppError

app = FastAPI(
    title="ticmymail-part2",
    version="0.1.0",
    openapi_tags=[
        {"name": "ingest", "description": "Incident ingestion"},
        {"name": "email", "description": "Outbound email"},
        {"name": "bigpanda", "description": "BigPanda integration"},
        {"name": "jira", "description": "Jira integration"},
        {"name": "meta", "description": "Health and version"},
    ],
)

app.include_router(ingest_router, prefix="/v1")
app.include_router(email_router, prefix="/v1")
app.include_router(bigpanda_router, prefix="/v1")
app.include_router(jira_router, prefix="/v1")
app.include_router(servicenow_router, prefix="/v1")
app.include_router(meta_router, prefix="/v1")


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    log_error(exc.message, error_code=exc.code, details={"path": str(request.url.path), "details": exc.details})
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request: Request, exc: RequestValidationError):
    payload = {
        "code": "INVALID_SCHEMA",
        "message": "Request validation failed",
        "details": exc.errors(),
    }
    log_error(payload["message"], error_code=payload["code"], details={"path": str(request.url.path), "details": exc.errors()})
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    payload = {
        "code": "UNEXPECTED_ERROR",
        "message": str(exc),
    }
    log_error(payload["message"], error_code=payload["code"], details={"path": str(request.url.path)})
    return JSONResponse(status_code=500, content=payload)
