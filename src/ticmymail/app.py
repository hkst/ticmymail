import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from .config import ConfigManager, ConfigError
from .dedupe import DedupeService, ADLSDedupeStore, InMemoryDedupeStore
from .email import EmailProvider, EmailSendError
from .integrations import BigPandaClient, BigPandaError


log = logging.getLogger("ticmymail")


class IncidentPayload(BaseModel):
    incident_id: str = Field(..., min_length=1)
    source: str
    details: dict


class EmailPayload(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    subject: str
    body: str
    message_id: str
    thread_id: str


class BigPandaPayload(BaseModel):
    host: str
    service: str
    status: str
    description: str


def create_app(config_root: str | Path = "/config") -> FastAPI:
    cm = ConfigManager(config_root)

    try:
        cfg = cm.app()
    except ConfigError as e:
        raise RuntimeError(f"Failed to load config: {e}")

    inc_dedupe_store = ADLSDedupeStore(cfg.get("dedupe_root", "/tmp/dedupe"))
    dedupe = DedupeService(inc_dedupe_store)
    email_provider_config = cm.email_provider()
    email_sender = EmailProvider(email_provider_config)
    bigpanda_client = BigPandaClient(cm.bigpanda())

    app = FastAPI(title="ticmymail", version=__import__("ticmymail").__version__)

    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/version")
    async def version():
        return {"version": app.version}

    @app.post("/v1/incidents/ingest")
    async def ingest(payload: IncidentPayload):
        body = payload.details
        dedupe_key = payload.incident_id

        is_dup = dedupe.is_duplicate(dedupe_key, body)
        if is_dup:
            return {"status": "duplicate", "incident_id": payload.incident_id}

        # business logic placeholder; store/notify etc.
        return {"status": "accepted", "incident_id": payload.incident_id}

    @app.post("/v1/comm/email")
    async def comm_email(payload: EmailPayload):
        data = payload.model_dump(by_alias=True)
        try:
            send_result = email_sender.send(data)
            return send_result
        except EmailSendError as e:
            log.error("Email send failed: %s", e)
            raise HTTPException(status_code=502, detail=str(e))

    @app.post("/v1/integrations/bigpanda/events")
    async def bigpanda(events: list[BigPandaPayload]):
        out = []
        for event in events:
            try:
                response = bigpanda_client.send_event(event.model_dump())
                out.append(response)
            except BigPandaError as e:
                raise HTTPException(status_code=400, detail=str(e))
        return {"results": out}

    return app
